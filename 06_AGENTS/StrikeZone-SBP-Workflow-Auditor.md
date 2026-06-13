---
type: strikezone-sbp-draft
status: draft / documentation-schema-pass
created: 2026-05-26
runtime: hermes-optimus
project: StrikeZone SBP
---

# StrikeZone SBP Workflow Auditor

## Purpose

The Workflow Auditor is the quality gate for StrikeZone SBP. It detects missing evidence, stale or unsupported claims, unsafe outputs, and authority violations before any operator-facing or public draft is considered review-ready.

## Blocking Conditions

A run is `blocked_review_required` when any of these are true:

- missing required TradingView screenshot for BTC/ETH/SOL D/4H/1H/15M;
- missing screenshot/provenance for CoinAnk when OI/CVD/funding/liquidity claims are made;
- exact price levels asserted without screenshot or source evidence;
- stale digest/session context used for the wrong session;
- social-only thesis with no chart/data confirmation;
- alt pick without BTC.D/TOTAL3/ETHBTC or breadth/flow confirmation;
- trade-plan draft lacks invalidation or no-trade rules;
- public Discord draft lacks NFA/thesis-assist framing;
- output attempts to execute, modify, or authorize trades;
- credential, token, or private account setting appears in captured content.

## Warning Conditions

- source timestamp unclear;
- TradingView interval label not verified;
- screenshot sidebar/toast obstruction detected;
- CoinAnk AI URL unresolved;
- YouTube/X source used as high-weight evidence;
- NotebookLM used as primary synthesis when ChaseOS evidence packet is available;
- macro calendar not checked before session trade-plan draft.

## Audit Checklist

```yaml
audit:
  required_screenshots:
    tradingview_btc_d_4h_1h_15m: pass|fail
    tradingview_eth_d_4h_1h_15m: pass|fail
    tradingview_sol_d_4h_1h_15m: pass|fail
    coinank_pro_chart_if_derivatives_claims: pass|fail|not_claimed
    coinank_heatmap_if_liquidity_claims: pass|fail|not_claimed
    funding_if_funding_claims: pass|fail|not_claimed
    oi_if_oi_claims: pass|fail|not_claimed
  provenance:
    every_source_has_url: pass|fail
    every_source_has_timestamp: pass|fail
    every_screenshot_has_path: pass|fail
  thesis_quality:
    chart_structure_present: pass|fail
    anchor_levels_verified_or_flagged: pass|fail
    invalidation_present: pass|fail
    no_trade_conditions_present: pass|fail
    confirmation_stack_present: pass|fail
  public_private_boundary:
    public_draft_no_private_entries: pass|fail
    private_trade_plan_separate: pass|fail
    nfa_framing_present: pass|fail
  authority:
    no_trade_execution: pass|fail
    no_account_mutation: pass|fail
    no_credential_capture: pass|fail
```

## Required Failure Language

- `NEEDS CHART/SNAPSHOT` — numeric chart levels or visible structures are not verified.
- `NEEDS HEATMAP SNAPSHOT` — liquidation/heatmap claim lacks current screenshot.
- `NEEDS OI/CVD/FUNDING SNAPSHOT` — derivatives claim lacks source proof.
- `NO HIGH-CONVICTION ALT SETUPS` — alt filter does not pass.
- `DRAFT ONLY — OPERATOR APPROVAL REQUIRED` — all Discord/public/trade outputs.

## Auditor Agent Role

The Risk Challenger / Workflow Auditor must attack the draft:

1. What is unsupported?
2. What evidence contradicts the thesis?
3. What stale data could mislead the session?
4. What would invalidate the idea?
5. What should be removed from public output?
6. What must Chaser.sol manually approve?

If unresolved, the run remains draft-only and blocked from public posting.
