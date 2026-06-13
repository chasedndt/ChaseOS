---
type: strikezone-sbp-draft
status: draft / documentation-schema-pass
created: 2026-05-26
runtime: hermes-optimus
project: StrikeZone SBP
---

# StrikeZone SBP Evidence Packet Template

```yaml
sbp_run:
  run_id: "YYYY-MM-DD-strikezone-session-001"
  generated_at: ""
  session: "asia | london_open | ny_open | london_close | ny_close | weekend | daily"
  mode: "manual_assisted | scheduled_draft | operator_approved"
  operator: "Chaser.sol"
  synthesis_mode: "chaseos_internal | notebooklm_fallback | comparison"
  source_surfaces:
    scheduled_digests: []
    social_analysis: []
    screeners: []
    tradingview: []
    derivatives_orderflow: []
    macro_etf_premium_calendar: []
    prompt_outputs: []
  markets:
    - symbol: "BTCUSDT"
      role: "market leader / risk-on risk-off anchor"
      screenshots:
        D: ""
        4H: ""
        1H: ""
        15M: ""
    - symbol: "ETHUSDT"
      role: "major alt / beta confirmation"
      screenshots:
        D: ""
        4H: ""
        1H: ""
        15M: ""
    - symbol: "SOLUSDT"
      role: "high-beta alt / momentum confirmation"
      screenshots:
        D: ""
        4H: ""
        1H: ""
        15M: ""
  breadth:
    btc_dominance: ""
    ethbtc: ""
    total2: ""
    total3: ""
  macro:
    dxy: ""
    us10y: ""
    ndx_spx: ""
    economic_calendar: ""
    btc_etf_flows: ""
    coinbase_premium: ""
  derivatives:
    funding: ""
    open_interest: ""
    cvd: ""
    volume_delta: ""
    long_short: ""
    liquidation_heatmap: ""
    orderbook_depth: ""
  thesis:
    market_regime: ""
    btc_bias: "bullish | bearish | neutral | wait"
    eth_bias: "bullish | bearish | neutral | wait"
    sol_bias: "bullish | bearish | neutral | wait"
    alt_watchlist: []
    confidence_score: 0
    invalidation: ""
    no_trade_conditions: []
  outputs:
    operator_brief: ""
    discord_draft: ""
    private_trade_plan: ""
  missing_data_flags: []
  contradictions: []
  provenance: []
```

## Evidence Card Index

| Source | Tier | URL | Screenshot | Card | Status |
|---|---:|---|---|---|---|
| TradingView BTC D | 1 | | | | pending |
| TradingView BTC 4H | 1 | | | | pending |
| TradingView BTC 1H | 1 | | | | pending |
| TradingView BTC 15M | 1 | | | | pending |
| CoinAnk Pro Chart | 2 | | | | pending |
| CoinAnk Heatmap | 2 | | | | pending |
| Farside BTC ETF | 3 | | | | pending |
| TradingDigits Coinbase Premium | 3 | | | | pending |
| Economic Calendar | 3 | | | | pending |
```
