"""AOR workflow handler for StrikeZone daily pre-brief acquisition (Pass 2).

Orchestration sequence:
    1. Load the base vault sources plan from strikezone-daily.json.
    2. Run all live acquisitions (AI queries, RSS feeds, web scrapes) and write
       results to staging. Failures in any category are non-fatal.
    3. Augment the plan with any successfully staged live sources.
    4. Validate the augmented plan and run the builder.
    5. Write source_packet + normalized_source_pack + briefing_ready_input_set
       artifacts and the stable latest-pointer file.

The latest-pointer file (runtime/acquisition/packs/strikezone-latest.json)
lets the 0600 ET sbp_strikezone_digest pipeline resolve the current pack
without hardcoding a date-stamped path.

Pass 2 extends live capture from AI queries only (Pass 1D) to include RSS/Atom
feeds and static web page scrapes via run_all_live_acquisitions(). All captured
content is staged before the builder runs — the builder remains a pure file
read layer.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from runtime.acquisition.builder import AcquisitionBuildError, SourcePackBuilder
from runtime.acquisition.live_sources import (
    run_all_live_acquisitions,
    staged_captures_to_source_dicts,
)
from runtime.acquisition.plan import validate_acquisition_plan
from runtime.acquisition.validators import AcquisitionValidationError

logger = logging.getLogger(__name__)


class WorkflowExecutionError(RuntimeError):
    """Fail-closed error for the strikezone_acquisition workflow."""


_PLAN_PATH = "runtime/acquisition/plans/strikezone-daily.json"


def _augment_plan_with_staged(plan_raw: dict[str, Any], staged_source_dicts: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a new plan dict augmented with staged live source entries.

    Adds each staged source to sources[] and its path to scope.read_scope[].
    Updates acquisition_surfaces and trust_floor to accommodate staged_capture
    sources. Returns the original plan_raw unchanged if staged_source_dicts is empty.
    """
    if not staged_source_dicts:
        return plan_raw

    import copy
    augmented = copy.deepcopy(plan_raw)

    # Extend sources
    existing_sources = list(augmented.get("sources") or [])
    augmented["sources"] = existing_sources + staged_source_dicts

    # Extend scope.read_scope with staging paths
    scope = augmented.setdefault("scope", {})
    read_scope = list(scope.get("read_scope") or [])
    for source in staged_source_dicts:
        path = source.get("path") or ""
        if path and path not in read_scope:
            read_scope.append(path)
    scope["read_scope"] = read_scope
    augmented["scope"] = scope

    # Ensure staged_capture is in acquisition_surfaces
    surfaces = list(augmented.get("acquisition_surfaces") or [])
    if "staged_capture" not in surfaces:
        surfaces.append("staged_capture")
    augmented["acquisition_surfaces"] = surfaces

    # Relax trust_floor to 3 to accept tier-3 AI-generated sources
    trust = dict(augmented.get("trust") or {})
    current_floor = int(trust.get("trust_floor") or 4)
    if current_floor < 3:
        trust["trust_floor"] = 3
    augmented["trust"] = trust

    return augmented


def run_strikezone_acquisition(inputs: dict[str, Any], vault_root: Path) -> dict[str, Any]:
    """Run StrikeZone daily acquisition with live source augmentation."""
    plan_file = vault_root / _PLAN_PATH
    if not plan_file.exists():
        raise WorkflowExecutionError(
            f"strikezone_acquisition: plan file not found at '{_PLAN_PATH}'"
        )

    try:
        plan_raw = json.loads(plan_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowExecutionError(
            f"strikezone_acquisition: plan file is not valid JSON: {exc}"
        ) from exc

    # Run all live acquisitions — graceful degrade on any failure
    # adapter_flags from the plan acts as per-category kill switch before any network call
    staged = run_all_live_acquisitions(
        vault_root,
        staging_subdir="strikezone",
        plan_id=plan_raw.get("plan_id", "strikezone-daily"),
        adapter_flags=plan_raw.get("adapter_flags") or {},
    )
    if staged:
        logger.info("strikezone_acquisition: captured %d live sources", len(staged))
    else:
        logger.info("strikezone_acquisition: no live sources captured (vault-only run)")

    staged_source_dicts = staged_captures_to_source_dicts(staged)
    plan_raw_augmented = _augment_plan_with_staged(plan_raw, staged_source_dicts)

    try:
        plan = validate_acquisition_plan(plan_raw_augmented)
        result = SourcePackBuilder().build_and_write(plan=plan, vault_root=vault_root)
    except (AcquisitionValidationError, AcquisitionBuildError) as exc:
        raise WorkflowExecutionError(f"strikezone_acquisition: {exc}") from exc

    return result.to_aor_result(
        objective={
            "title": plan.objective,
            "requested_by": plan.requested_by,
            "downstream_target": plan.downstream_target,
        },
        project_scope="StrikeZone",
        live_source_count=len(staged),
    )
