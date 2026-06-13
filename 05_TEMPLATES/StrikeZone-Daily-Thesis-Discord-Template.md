---
type: strikezone-sbp-draft
status: draft / documentation-schema-pass
created: 2026-05-26
runtime: hermes-optimus
project: StrikeZone SBP
---

# StrikeZone Daily Thesis Discord Template

```md
📊 StrikeZone Daily Thesis — {{date}} / {{session}}
Status: DRAFT / thesis-assist. Not financial advice. Operator approval required.

Market read:
{{market_regime_summary}}

BTCUSDT
Bias: {{btc_bias}} / Confidence: {{btc_confidence}}
HTF: {{btc_htf_structure}}
Execution: {{btc_ltf_trigger_or_wait}}
Invalidation: {{btc_invalidation}}
No-trade: {{btc_no_trade_conditions}}
Screenshots: D / 4H / 1H / 15M captured.

ETHUSDT
Bias: {{eth_bias}} / Confidence: {{eth_confidence}}
Reason: {{eth_reason}}
Invalidation: {{eth_invalidation}}
Screenshots: D / 4H / 1H / 15M captured.

SOLUSDT
Bias: {{sol_bias}} / Confidence: {{sol_confidence}}
Reason: {{sol_reason}}
Invalidation: {{sol_invalidation}}
Screenshots: D / 4H / 1H / 15M captured.

Alt watchlist:
{{alt_watchlist_or_no_high_conviction_alt_setups}}

Confirmation gates:
- {{gate_1}}
- {{gate_2}}
- {{gate_3}}

Missing data / caution:
{{missing_data_flags}}

NFA. This is a structured market read and thesis-support draft, not an automated signal or trade execution instruction.
```

## Public Safety Rules

- Do not include private account balances, leverage, exact position details, or private trade execution plans.
- Include invalidation and no-trade language.
- Include NFA/thesis-assist framing.
- If confidence is low or evidence missing, say wait/no trade.
- Public draft never posts itself; operator approval required.
