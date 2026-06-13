"""Adjacent adapter-health rollup for runtime provider-status.

This module reads connector-health and delivery-health telemetry as adjacent
adapter evidence. It intentionally does not read or write provider-state
fallback governance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


LANE_KEYS = ("connector_health", "delivery_health")
STATUS_NAMES = ("failed", "skipped", "succeeded")


def _empty_counts() -> dict[str, int]:
    return {status: 0 for status in STATUS_NAMES}


def _coerce_counts(value: Any) -> dict[str, int]:
    counts = _empty_counts()
    if isinstance(value, dict):
        for status in STATUS_NAMES:
            counts[status] = int(value.get(status) or 0)
    return counts


def _connector_lane(vault_root: Path, limit: int) -> tuple[dict[str, Any], list[str]]:
    from runtime.acquisition.connector_health import summarize_connector_health

    summary = summarize_connector_health(vault_root, limit=limit)
    surfaces = []
    for connector_id, item in sorted((summary.get("connectors") or {}).items()):
        latest = item.get("latest_event") or {}
        surfaces.append(
            {
                "lane": "connector_health",
                "surface_id": connector_id,
                "surface_kind": "acquisition_connector",
                "event_count": int(item.get("event_count") or 0),
                "status_counts": _coerce_counts(item.get("status_counts")),
                "latest_event": latest,
                "latest_status": latest.get("status"),
                "latest_failure_reason": latest.get("failure_reason"),
            }
        )
    return {
        "lane": "connector_health",
        "status": _lane_status(summary),
        "summary": summary,
        "surfaces": surfaces,
    }, []


def _delivery_lane(vault_root: Path, limit: int) -> tuple[dict[str, Any], list[str]]:
    from runtime.sbp.delivery_health import summarize_delivery_health

    summary = summarize_delivery_health(vault_root, limit=limit)
    surfaces = []
    for adapter_id, item in sorted((summary.get("adapters") or {}).items()):
        latest = item.get("latest_event") or {}
        surfaces.append(
            {
                "lane": "delivery_health",
                "surface_id": adapter_id,
                "surface_kind": "delivery_adapter",
                "event_count": int(item.get("event_count") or 0),
                "status_counts": _coerce_counts(item.get("status_counts")),
                "latest_event": latest,
                "latest_status": latest.get("status"),
                "latest_failure_reason": latest.get("failure_reason"),
            }
        )
    return {
        "lane": "delivery_health",
        "status": _lane_status(summary),
        "summary": summary,
        "surfaces": surfaces,
    }, []


def _error_lane(lane: str, exc: Exception) -> dict[str, Any]:
    return {
        "lane": lane,
        "status": "read_error",
        "summary": {
            "schema_version": 1,
            "exists": None,
            "event_count": 0,
            "status_counts": _empty_counts(),
            "error": f"{type(exc).__name__}: {exc}",
        },
        "surfaces": [],
    }


def _lane_status(summary: dict[str, Any]) -> str:
    counts = _coerce_counts(summary.get("status_counts"))
    event_count = int(summary.get("event_count") or 0)
    if event_count == 0:
        return "no_events"
    if counts["failed"]:
        return "attention"
    if counts["skipped"]:
        return "observed_skips"
    return "healthy"


def _overall_status(lanes: dict[str, dict[str, Any]], totals: dict[str, int]) -> str:
    if any(lane.get("status") == "read_error" for lane in lanes.values()):
        return "degraded"
    if totals["event_count"] == 0:
        return "no_events"
    if totals["failed_count"]:
        return "attention"
    if totals["skipped_count"]:
        return "observed_skips"
    return "healthy"


def build_adapter_health_rollup(vault_root: str | Path, *, limit: int = 200) -> dict[str, Any]:
    """Build a read-only adjacent health summary for non-provider adapters."""
    root = Path(vault_root)
    warnings: list[str] = []
    lane_builders = {
        "connector_health": _connector_lane,
        "delivery_health": _delivery_lane,
    }
    lanes: dict[str, dict[str, Any]] = {}
    surfaces: list[dict[str, Any]] = []
    totals = {
        "event_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "succeeded_count": 0,
        "surface_count": 0,
    }

    for lane_key in LANE_KEYS:
        try:
            lane, lane_warnings = lane_builders[lane_key](root, limit)
        except Exception as exc:  # adjacent telemetry must not break provider-status
            lane = _error_lane(lane_key, exc)
            lane_warnings = [f"{lane_key} read failed: {type(exc).__name__}: {exc}"]
        lanes[lane_key] = lane
        warnings.extend(lane_warnings)
        summary = lane.get("summary") or {}
        counts = _coerce_counts(summary.get("status_counts"))
        totals["event_count"] += int(summary.get("event_count") or 0)
        totals["failed_count"] += counts["failed"]
        totals["skipped_count"] += counts["skipped"]
        totals["succeeded_count"] += counts["succeeded"]
        lane_surfaces = list(lane.get("surfaces") or [])
        surfaces.extend(lane_surfaces)
        totals["surface_count"] += len(lane_surfaces)

    return {
        "schema_version": 1,
        "status": _overall_status(lanes, totals),
        "source": "connector_health_and_delivery_health_ledgers",
        "read_only": True,
        "provider_state_boundary": {
            "feeds_provider_state_ledger": False,
            "controls_provider_switching": False,
            "controls_cooldowns": False,
            "controls_recovery_to_primary": False,
        },
        "totals": totals,
        "lanes": lanes,
        "surfaces": surfaces,
        "warnings": warnings,
    }
