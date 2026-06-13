"""
runtime.operator_surface.planner

FSOS Planner — translates a natural language operator goal into an ordered
list of typed steps for the executor to run.

The planner is the PLAN mode of the operator overlay.
It produces a plan before any execution begins.
The plan is emitted as a PLAN_READY event before the first step executes.

Planning strategy:
- In Phase 9 foothold: planner is a placeholder; steps are declared in workflow manifest
- In later passes: planner may use AOR-dispatched model call to generate steps from goal
- In either case: steps must conform to the surface adapter's capability declarations

Planner defined in: 06_AGENTS/Full-System-Operator-Surface.md Section 6
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from runtime.operator_surface.contracts import OperatorScope, OperatorRunAudit
from runtime.operator_surface.capabilities import OperatorCapability, SurfaceType
from runtime.operator_surface.events import OperatorEvent, OperatorEventType


class OperatorPlanner:
    """
    Produces an execution plan (ordered list of steps) from a goal + scope.

    Phase 9 foothold: accepts explicitly declared steps from the workflow manifest.
    Future: uses a model call to generate steps dynamically from a natural language goal.

    The planner does NOT execute steps — that is the executor's job.
    The planner is called once before execution begins.
    """

    def plan_from_manifest_steps(
        self,
        steps: list[dict],
        scope: OperatorScope,
        goal: str,
    ) -> list[dict]:
        """
        Accept pre-declared steps from a workflow manifest.
        Validates that each step has required fields before accepting.
        Returns the validated step list.
        """
        validated = []
        for i, step in enumerate(steps):
            if not step.get("action_type"):
                raise ValueError(f"Step {i} missing required field 'action_type'")
            if not step.get("target"):
                raise ValueError(f"Step {i} missing required field 'target'")
            # Enrich step with index
            enriched = dict(step)
            enriched["step_index"] = i
            enriched["goal"] = goal
            validated.append(enriched)
        return validated

    def build_plan_ready_event(
        self,
        run_id: str,
        surface: str,
        plan: list[dict],
        goal: str,
    ) -> OperatorEvent:
        """Build the PLAN_READY event that is emitted before execution begins."""
        return OperatorEvent(
            event_id=str(uuid.uuid4()),
            run_id=run_id,
            surface=surface,
            event_type=OperatorEventType.PLAN_READY,
            timestamp=datetime.now(timezone.utc).isoformat(),
            step_index=0,
            description=f"Plan ready: {len(plan)} steps for goal: {goal}",
            payload={"plan": plan, "total_steps": len(plan)},
        )
