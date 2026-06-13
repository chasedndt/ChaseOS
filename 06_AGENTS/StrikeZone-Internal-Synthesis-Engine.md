---
type: strikezone-sbp-draft
status: draft / documentation-schema-pass
created: 2026-05-26
runtime: hermes-optimus
project: StrikeZone SBP
---

# StrikeZone Internal Synthesis Engine

## Purpose

The StrikeZone Internal Synthesis Engine is the ChaseOS-owned replacement path for NotebookLM as the primary summarization/thesis engine.

NotebookLM status:
- current: useful manual condenser/comparison surface;
- future: optional/legacy/fallback;
- not a permanent required dependency.

## Inputs

The engine consumes governed evidence packets, not raw browser state directly:

- scheduled digest markdown/cards from Grok, Perplexity, ChatGPT;
- screenshot-to-markdown evidence cards from TradingView, CoinAnk, screeners, social surfaces;
- prompt outputs from the versioned StrikeZone prompt registry;
- operator notes;
- source registry weights and freshness metadata;
- missing-data / contradiction reports from the Workflow Auditor.

## Model Lane

Primary future lane: configured ChaseOS strong model stack such as GPT-5.5 or the active provider-governed model lane. The model provider does not own truth; ChaseOS owns evidence, provenance, and output state.

Fallbacks:
- NotebookLM manual synthesis export;
- Grok/Perplexity/ChatGPT scheduled output as separate evidence, not authority;
- local models only if configured and quality-gated.

## Processing Stages

1. Normalize evidence cards into one SBP evidence packet.
2. Sort evidence by tier, freshness, and session relevance.
3. Extract mandatory structures: HTF bias, LTF trigger, key levels, invalidation, no-trade conditions, derivative confirmation/contradiction, macro risk.
4. Run missing-data checks before thesis generation.
5. Run contradiction checks before confidence scoring.
6. Generate session thesis draft.
7. Generate risk challenge.
8. Generate public Discord draft and separate private operator/trade-plan drafts.
9. Route all outputs to draft/log surfaces.

## Required Outputs

- evidence packet path;
- contradiction report;
- missing-data checklist;
- BTC/ETH/SOL session thesis;
- optional alt watchlist only if strict filter passes;
- Discord draft;
- private operator brief;
- private trade-plan draft;
- provenance list.

## Non-Truth Rules

- Chatbot output cannot set bias alone.
- NotebookLM summary cannot override TradingView/CoinAnk evidence.
- Numeric levels must be supported by screenshot/evidence or marked `NEEDS CHART/SNAPSHOT`.
- OI/CVD/funding claims require CoinAnk screenshot/card or equivalent explicit source.
- Alts require breadth/flow confirmation, not social hype.

## Implementation Interface Draft

```yaml
synthesis_run:
  run_id: "YYYY-MM-DD-strikezone-session-001"
  model_lane: "configured_chaseos_strong_model"
  notebooklm_mode: "disabled | fallback | comparison"
  input_packet: "05_TEMPLATES/StrikeZone-SBP-Evidence-Packet-Template-derived-output.md"
  source_registry: "06_AGENTS/StrikeZone-SBP-Source-Registry.md"
  workflow_auditor: "06_AGENTS/StrikeZone-SBP-Workflow-Auditor.md"
  outputs:
    operator_brief: "07_LOGS/Operator-Briefs/StrikeZone/<run_id>.md"
    discord_draft: "07_LOGS/Operator-Briefs/StrikeZone/<run_id>_discord_draft.md"
    private_trade_plan: "07_LOGS/Operator-Briefs/StrikeZone/<run_id>_private_trade_plan.md"
    audit_log: "07_LOGS/Agent-Activity/StrikeZone/<run_id>.md"
```

## Replacement Roadmap

Stage 1: manual NotebookLM allowed; ChaseOS stores evidence packets and drafts.
Stage 2: ChaseOS synthesis runs in parallel with NotebookLM for comparison.
Stage 3: ChaseOS synthesis becomes default; NotebookLM used only for manual fallback.
Stage 4: Workflow Auditor blocks thesis drafts that rely on NotebookLM without source evidence.
