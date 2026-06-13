"""
runtime/sbp — Scheduled Briefing Pipeline (SBP) Substrate

Phase 9 Pass 1A — Generic SBP substrate. Not coupled to any specific pipeline
instance. StrikeZone Market Digest Publisher and other instance pipelines sit
on top of this substrate layer (Pass 1B+).

Core modules:
    manifest        — SBPConfig dataclass + sbp_config block validator
    guardrail       — write scope enforcement + pipeline runnability check
    input_adapters  — InputAdapter ABC + VaultNotesInputAdapter + stubs
    delivery_adapters — DeliveryAdapter ABC + VaultLocalDeliveryAdapter + stubs
    base_handler    — SBPBaseHandler ABC for instance pipeline handlers
    runner          — run_sbp_pipeline() generic stub runner (AOR Stage 6 fallback)
"""
