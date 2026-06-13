---
type: strikezone-sbp-draft
status: draft / documentation-schema-pass
created: 2026-05-26
runtime: hermes-optimus
project: StrikeZone SBP
---

# StrikeZone Operator Trade Plan Template

Private draft only. Never post publicly by default. Never execute automatically.

```yaml
trade_plan:
  run_id: ""
  asset: "BTCUSDT | ETHUSDT | SOLUSDT | other"
  direction: "long | short | wait"
  setup_type: "sweep_reclaim | break_retest | vwap_reclaim | range_reversion | continuation | no_trade"
  thesis_reference: ""
  evidence_packet: ""
  entry_trigger:
    required_zone_tap: ""
    required_ltf_signal: "5m/15m CHOCH/MSB close, sweep/reclaim, divergence, etc."
    required_orderflow: "OI spike, CVD confirmation/divergence, funding/heatmap condition"
  invalidation: ""
  stop_band: "draft only"
  take_profit:
    tp1: "draft only"
    tp2: "draft only"
    runner: "draft only"
  trailing_logic: "draft only"
  no_trade_conditions: []
  confidence_score: 0
  manual_execution_surface: "Hyperliquid / Drift / other — operator confirms manually"
  approval_status: "draft_only | operator_reviewed | rejected"
```

## Required Sections

### Setup Summary

### Entry Trigger

### Invalidation

### Stop / Take-Profit Draft

### No-Trade Conditions

### Evidence Links

### Operator Decision

- [ ] approve manually
- [ ] reject
- [ ] needs more evidence
- [ ] watch only

Hard rule: no private trade-plan draft is valid without invalidation and no-trade conditions.
