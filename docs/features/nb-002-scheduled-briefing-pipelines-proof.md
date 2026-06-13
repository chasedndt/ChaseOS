# NB-002 Scheduled Briefing Pipelines — Readiness Matrix Proof

Generated: 2026-06-12T14:34:03+01:00
Backlog item: NB-002 — Scheduled Briefing Pipelines expansion
Product surfaces: Proactive Briefings, Schedules, Review Queue

## Safe slice delivered

`runtime.studio.schedule_inspector.get_schedule_summary()` now includes a `briefing_pipeline_expansion` UI contract for the Schedules/Proactive Briefings surface. The contract filters the local schedule intents down to operator briefing and Scheduled Briefing Pipeline routines, then exposes schedule count, enabled/paused state, external-delivery declaration count, Review Queue visibility, per-routine cadence/runtime/delivery posture, and the lower-authority lane that remains blocked.

This is a read-only/status slice. It does not enable or disable schedules, start a daemon, dispatch a runtime, write queue work, consume approvals, call providers, deliver externally, or promote canonical knowledge.

## Verification command

```bash
PYTHONPATH=. uvx --with pyyaml python - <<'PY'
from pathlib import Path
from runtime.studio.schedule_inspector import get_schedule_summary
vault = Path('.').resolve()
summary = get_schedule_summary(vault)
expansion = summary['briefing_pipeline_expansion']
print('ok=', summary['ok'])
print('briefing_schedule_count=', expansion['schedule_count'])
print('enabled=', expansion['enabled_schedule_count'])
print('paused=', expansion['paused_schedule_count'])
print('external_delivery_declared=', expansion['external_delivery_declared_count'])
print('review_queue_visible=', expansion['review_queue_visible_count'])
for row in expansion['rows']:
    print(f"- {row['schedule_id']} | {row['workflow_id']} | {row['family']} | enabled={row['enabled']} | review={row['review_posture']}")
PY
```

## Observed output

```text
ok= True
briefing_schedule_count= 3
enabled= 2
paused= 1
external_delivery_declared= 1
review_queue_visible= 1
- sch-operator-close-day-1900 | operator_close_day | Operator Briefing | enabled=True | review=Vault-local routine
- sch-operator-today-0700 | operator_today | Operator Briefing | enabled=True | review=Vault-local routine
- sch-sbp-strikezone-digest-0600 | sbp_strikezone_digest | Scheduled Briefing Pipeline | enabled=False | review=Review Queue visible
```

## UI contract fields

The `briefing_pipeline_expansion` block includes:

- `backlog_id`: `NB-002`
- `product_surfaces`: `Proactive Briefings`, `Schedules`, `Review Queue`
- `schedule_count`, `enabled_schedule_count`, `paused_schedule_count`
- `external_delivery_declared_count`
- `review_queue_visible_count`
- `families`
- `rows[]` with `schedule_id`, `workflow_id`, `family`, `enabled`, `cadence_type`, `cron_expression`, `timezone`, `runtime_adapter_target`, `runtime_adapter_fallback`, `delivery_primary_target`, `vault_local_only`, `external_delivery_declared`, `approval_policy`, `review_queue_visible`, and `review_posture`
- `blocked_lower_authority_lane`

## Authority boundary preserved

Live schedule activation, runtime dispatch, queue writes, provider calls, external delivery, approval consumption, and canonical promotion remain in governed Phase 9 lanes. This proof only makes the briefing pipeline posture visible to the operator.
