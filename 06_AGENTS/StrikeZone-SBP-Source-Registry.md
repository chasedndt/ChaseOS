---
type: strikezone-sbp-draft
status: draft / documentation-schema-pass
created: 2026-05-26
runtime: hermes-optimus
project: StrikeZone SBP
---

# StrikeZone SBP Source Registry

This registry preserves the exact sources from the handover and classifies them for evidence weight, capture type, and implementation risk.

## Source Weight Classes

- Tier 1: TradingView marked structure and user chart screenshots.
- Tier 2: CoinAnk derivatives/orderflow/liquidity data.
- Tier 3: ETF flows, Coinbase premium, macro/economic calendar, cross-asset context.
- Tier 4: Altfins / MarketMasters / screeners.
- Tier 5: YouTube / X / TrackFi / TradingView Ideas.
- Tier 6: Grok/Perplexity/ChatGPT scheduled outputs, Google Docs prompts, NotebookLM.

## YouTube Trader / Analyst Sources

| Source | URL | Use | Capture expectation | Tier |
|---|---|---|---|---|
| The Trading Parrot | https://www.youtube.com/@TheTradingParrot | title/feed scan for current market prep | subscription feed screenshot + selected video metadata/transcript only if relevant | 5 |
| BitcoinHyper | https://www.youtube.com/@BitcoinHyper | BTC/current-market commentary | feed screenshot + selected metadata | 5 |
| Cilinix Crypto | https://www.youtube.com/@CilinixCrypto | crypto market commentary | feed screenshot + selected metadata | 5 |
| Mister Crypto | https://www.youtube.com/@MisterCrypto | BTC/market structure commentary | feed screenshot + selected metadata | 5 |
| Crypto World Josh | https://www.youtube.com/@CryptoWorldJosh | BTC/ETH technical context | feed screenshot + selected metadata | 5 |
| MegaWhale Crypto | https://www.youtube.com/@MegaWhaleCrypto | whale/narrative context | feed screenshot + selected metadata | 5 |
| CryptoCobra | https://www.youtube.com/@CryptoCobra- | market commentary | feed screenshot + selected metadata | 5 |
| stackersatoshi | https://www.youtube.com/@stackersatoshi | BTC narrative/context | feed screenshot + selected metadata | 5 |
| Thomas Boleto Trader | https://www.youtube.com/@ThomasBoletoTrader | trader view / market prep | feed screenshot + selected metadata | 5 |
| Michael Pizzino | https://www.youtube.com/@MichaelPizzino | macro/crypto cycle context | feed screenshot + selected metadata | 5 |

Rule: do not watch/summarize every video blindly. Prefer recent videos whose title/thumbnail indicates current BTC/ETH/SOL, premarket, rotation, or macro relevance.

## Social / Analyst Aggregation / Prompt Surfaces

| Source | Exact URL | Use | Capture expectation | Tier |
|---|---|---|---|---|
| X timeline | https://x.com/i/timeline | curated X feed from logged-in account | screenshot/card of relevant public posts; no private DMs unless separately scoped | 5 |
| ChaserCrypto profile | https://x.com/ChaserCrypto_ | account/feed context | public profile/feed screenshot when relevant | 5 |
| TrackFi | https://app.trackfi.ai/ | analyst/social aggregation | dashboard screenshot + visible source cards | 5 |
| NotebookLM | https://notebooklm.google.com/?original_referer=https%3A%2F%2Fnotebooklm.google%23&pli=1&authuser=1&pageId=none | optional legacy/fallback synthesis | export/screenshot of notebook output only; not source of truth | 6 |
| Google Docs prompt library | https://docs.google.com/document/d/1lErOGSZkLAuLClREKK_5K2zGflwAveAC5hxMVIdamdY/edit?usp=sharing | crypto LLM mega prompts | versioned prompt snapshot/export; never store credentials | 6 |

## Screener / Trend / AI Analysis Sources

| Source | URL | Use | Capture expectation | Tier |
|---|---|---|---|---|
| Altfins crypto screener | https://altfins.com/crypto-screener | breadth/rotation/high-liquidity alt scan | screenshot + filter metadata | 4 |
| MarketMasters.ai | https://marketmasters.ai/ | market/trend summary | dashboard screenshot + visible claims | 4 |
| TradingView Crypto Ideas | https://www.tradingview.com/ideas/cryptocurrencies/ | public chart ideas/consensus | screenshot + selected idea links | 5 |
| CoinAnk AI generator | coinankai.com (unverified) | possible AI market generator | exact URL must be operator-verified before manifest use | 4/6 pending |

Decision: `coinankai.com` remains unresolved and must be verified during implementation; do not conflate it with CoinAnk Pro Chart.

## TradingView Chart Sources

| Source | URL pattern | Use | Capture expectation | Tier |
|---|---|---|---|---|
| TradingView chart | https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=D | BTC/ETH/SOL marked structure | D/4H/1H/15M screenshot with sidebar closed, fit/reset view, interval verified | 1 |

Core symbols:
- `BINANCE:BTCUSDT`
- `BINANCE:ETHUSDT`
- `BINANCE:SOLUSDT`

Core timeframes:
- `D`, `4H`, `1H`, `15M`

Optional timeframes: `5M`, `30M`, `2H`, `8H`.

## CoinAnk / Derivatives / Liquidity Sources

| Source | URL | Use | Capture expectation | Tier |
|---|---|---|---|---|
| CoinAnk Pro Chart BTC 15m | https://coinank.com/proChart?exchange=Binance&symbol=BTCUSDT&productType=SWAP&interval=15m | VWAP/CVD/OI/funding/orderbook/depth confirmation | screenshot + evidence card | 2 |
| Raw provided Pro Chart URL | https://coinank.com/proChart? exchange=Binance&symbol=BTCUSDT&productType=SWAP&interval=15m | provenance of original pasted link | preserve raw string; normalized version above for implementation | 2 |
| Liquidation heatmap | https://coinank.com/chart/derivatives/liq-heat-map/btcusdt/12h | liquidation shelves/magnets | heatmap screenshot required before claims | 2 |
| Funding rates | https://coinank.com/fundingRate/current | funding/crowding | screenshot/table card | 2 |
| Long/short realtime | https://coinank.com/longshort/realtime | positioning skew | screenshot/table card | 2 |
| Hyperliquid | https://coinank.com/hyperliquid | HL whale/flow context | screenshot/card | 2 |
| Orderbook Pro depth | https://coinank.com/orderbookPro/depth | bid/ask depth and imbalance | screenshot/card | 2 |
| OI screener | https://coinank.com/screener/oi | market-wide OI shifts | screenshot/card | 2 |

CoinAnk indicators to preserve when visible:
- VWAP
- Delta Bars, Perpetuals
- Aggregated CVD, Perpetuals
- Aggregated Taker B/S Value, Perpetuals
- Aggregated OrderBook Depth Delta, Perpetuals
- Open Interest Delta
- Aggregated Open Interest K-line
- Aggregated Open Interest RSI
- Open Interest Weighted Funding Rates

## ETF / Coinbase Premium / Macro Calendar Sources

| Source | URL | Use | Capture expectation | Tier |
|---|---|---|---|---|
| Farside BTC ETF flows | https://farside.co.uk/btc/ | BTC ETF inflows/outflows | screenshot/table + latest date | 3 |
| TradingDigits Coinbase Premium | https://www.tradingdigits.io/coinbase-premium | Coinbase/US spot premium | screenshot/card + timestamp | 3 |
| TradingDigits Economic Calendar | https://www.tradingdigits.io/economicCalendar | macro event risk/fakeout windows | screenshot/calendar + session date | 3 |

## Action / Trade-Plan Surfaces

Named but URL-unresolved:
- Hyperliquid
- BTC-PERP / Drift Protocol
- Live Trade Chat
- LTF Crypto Trading Assistant
- Claude — LTF market analysis

Decision: do not invent action URLs. During implementation, capture exact URLs from operator bookmarks/logged-in browser. These remain manual/private and draft-only.

## Source Registry Decisions

1. TradingView screenshots and CoinAnk orderflow screenshots are mandatory proof for claims that depend on charts or derivatives.
2. X/YouTube/TrackFi/TradingView Ideas are consensus/context only.
3. Scheduled-search outputs and NotebookLM are Tier 6 synthesis aids.
4. NotebookLM is optional/fallback, not a required future core.
5. CoinAnk AI URL is unresolved and blocked pending operator verification.
6. Any logged-in source may be captured visually only under operator-routed scope; no credential extraction or storage.
