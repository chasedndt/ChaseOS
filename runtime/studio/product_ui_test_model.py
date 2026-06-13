"""Deterministic ChaseOS Studio product UI test model.

The model is intentionally local, synthetic, and side-effect free. It gives the
Browser Runtime a realistic product UI surface to inspect without pointing
automation at accounts, credentials, live workflows, or canonical writeback.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.product_ui_test_model.v1"
SURFACE_ID = "chaseos_studio_product_ui_test_target"
PANEL_ID = "studio-safe-browser-proof-sandbox"
ROUTE_HINT = "#safe-browser-proof"
SURFACE_LABEL = "Safe Browser Proof Sandbox"


@dataclass(frozen=True)
class ProductUITestTask:
    task_id: str
    label: str
    lane: str
    owner: str
    status: str
    risk: str


@dataclass(frozen=True)
class ProductUITestApproval:
    approval_id: str
    surface: str
    status: str
    authority: str
    writes_allowed: bool


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_product_ui_test_model(vault_root: str | Path) -> dict[str, Any]:
    """Return deterministic product UI state for browser-runtime proofs."""
    vault = Path(vault_root).resolve()
    tasks = [
        ProductUITestTask(
            task_id="bosl-001",
            label="Validate product UI target contract",
            lane="Browser Runtime",
            owner="Codex",
            status="ready",
            risk="low",
        ),
        ProductUITestTask(
            task_id="studio-014",
            label="Review local app registry boundary",
            lane="Studio",
            owner="Hermes",
            status="waiting",
            risk="medium",
        ),
        ProductUITestTask(
            task_id="siteops-022",
            label="Keep skill promotion inactive",
            lane="SiteOps",
            owner="OpenClaw",
            status="blocked",
            risk="high",
        ),
    ]
    approvals = [
        ProductUITestApproval(
            approval_id="apr-shadow-001",
            surface="Browser proof",
            status="pending_review",
            authority="draft evidence only",
            writes_allowed=False,
        ),
        ProductUITestApproval(
            approval_id="apr-studio-002",
            surface="Studio test target",
            status="safe_mode",
            authority="local UI only",
            writes_allowed=False,
        ),
    ]
    return {
        "ok": True,
        "model_version": MODEL_VERSION,
        "surface": SURFACE_ID,
        "title": "ChaseOS Studio Safe Browser Proof Sandbox",
        "surface_label": SURFACE_LABEL,
        "panel_id": PANEL_ID,
        "route_hint": ROUTE_HINT,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "safe_mode": True,
        "target_family": "vincisos-product-ui browser-runtime-product-target",
        "proof_contract": "vincisos.full_ui_target.v1",
        "metrics": {
            "runtime_panels": 5,
            "pending_approvals": 2,
            "blocked_effects": 12,
            "draft_candidates": 3,
        },
        "tasks": [asdict(task) for task in tasks],
        "approvals": [asdict(approval) for approval in approvals],
        "warnings": [],
        "empty_state": {
            "tasks": "No browser proof tasks are queued for this sandbox.",
            "approvals": "No approvals are actionable from this read-only Studio sandbox.",
            "blocked_backend_execution": "Browser automation, Agent Bus enqueue, approval execution, and canonical writeback require lower-phase governed contracts; this sandbox only supports client-side inspection.",
        },
        "selectors": {
            "root": "[data-testid='studio-product-ui-root']",
            "safe_mode_banner": "[data-testid='safe-mode-banner']",
            "overview_tab": "[data-testid='tab-overview']",
            "approvals_tab": "[data-testid='tab-approvals']",
            "workflow_tab": "[data-testid='tab-workflow']",
            "task_table": "[data-testid='task-table']",
            "approval_table": "[data-testid='approval-table']",
            "harmless_action": "[data-testid='harmless-inspect-action']",
            "status_output": "[data-testid='action-status']",
        },
        "authority": {
            "local_only": True,
            "safe_mode_only": True,
            "read_only_model": True,
            "writes_vault": False,
            "starts_workflows": False,
            "browser_automation_authorized_by_app": False,
            "provider_calls_allowed": False,
            "agent_bus_enqueue_allowed": False,
            "gate_mutation_allowed": False,
            "canonical_writeback_allowed": False,
            "credential_or_cookie_access_allowed": False,
            "skill_activation_allowed": False,
        },
        "allowed_harmless_actions": [
            {
                "action_id": "mark-panel-inspected",
                "label": "Mark panel inspected",
                "client_side_only": True,
                "writes_vault": False,
                "network_request": False,
                "expected_status_text": "Panel inspected in safe mode.",
            }
        ],
    }
