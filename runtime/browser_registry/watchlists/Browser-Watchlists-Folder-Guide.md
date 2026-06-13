# runtime/browser_registry/watchlists/

> Watchlist definitions for bounded browser monitoring tasks.
> Each watchlist entry should be machine-readable, origin-scoped, and tied to a declared task class.

## Intended Use

Use this folder for watchlisted public pages that a runtime may monitor for:
- title changes
- visible-text changes
- known-selector changes
- evidence screenshot capture

## Rules

1. Each watchlist entry must name its task class from `runtime/browser_registry/task_classes.yaml`.
2. Each watchlist entry must reference an allowed origin group from `runtime/browser_registry/allowed_origins.yaml`.
3. Watchlists are for public, bounded sources only.
4. Watchlists do not authorize recursive crawling, login, downloads, or form submission.
5. Outputs must remain compatible with current markdown index surfaces and future standalone runtime views.

### Summary-context application
For how watchlist entries, monitored-source checks, and browser-derived evidence outputs should become typed human-facing summaries in future standalone surfaces, see:
- `06_AGENTS/Browser-Watchlists-and-Evidence-Flow-Summary-Context-Application.md`

## Suggested Entry Fields

```yaml
id: example-watchlist
origin_group: public-status-and-monitoring
task_class: watchlisted_page_change_monitor
urls: []
change_criteria:
  - title
  - visible_text
output_target: 07_LOGS/Operator-Briefs/
notes: >-
  Keep output index-friendly and standalone-portable.
```

*Graph links: [[OpenClaw-Runtime-Profile]] · [[Browser-Autonomy-Policy]] · [[Browser-Task-Patterns]] · [[06_AGENTS/Vault-Map|Vault-Map]]*
