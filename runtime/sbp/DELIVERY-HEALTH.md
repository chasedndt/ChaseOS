---
title: SBP Delivery Health Telemetry
type: runtime-reference
status: active
created: 2026-04-28
updated: 2026-04-28
---

# SBP Delivery Health Telemetry

SBP delivery-health is the runtime-local telemetry layer for external delivery adapters.
It records whether an SBP output delivery attempt succeeded, failed, or was skipped after
content generation and bounded vault writeback.

Ledger path:

```text
runtime/sbp/state/delivery_health_events.jsonl
```

CLI inspection:

```powershell
chaseos sbp delivery-health --json
chaseos sbp delivery-health --adapter discord --limit 10 --json
chaseos sbp delivery-health --adapter whop --limit 10 --json
```

Current emitters:

- `DiscordDeliveryAdapter` records missing webhook env var, HTTP/network/Gate failure, and successful webhook delivery.
- `WhopDeliveryAdapter` records missing API key env var, missing manifest `channel_id`, HTTP/network/Gate failure, and successful forum-post delivery.

Boundary:

- Delivery-health is not provider-state fallback governance.
- It does not switch providers, choose models, enforce cooldowns, clean queues, retry delivery, or recover to primary.
- It does not persist webhook URLs or API keys; event targets use safe references such as `env:STRIKEZONE_DISCORD_WEBHOOK_URL` or `whop-forum:exp_...`.
- Delivery adapters emit events fail-open when `vault_root` is present in delivery context. Telemetry write failure does not convert delivery into a pipeline failure.

Related surfaces:

- `runtime/sbp/delivery_adapters.py`
- `runtime/providers/provider_call_surfaces.json`
- `runtime/providers/README.md`
- `runtime/cli/main.py`
