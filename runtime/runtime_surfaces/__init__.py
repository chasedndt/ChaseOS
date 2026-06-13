"""Adaptive Runtime Surface Layer manifest registry.

Phase 1 is intentionally read-only: it validates runtime surface metadata and
loads first-party manifests. Execution and routing authority stays with the
existing provider, AOR, Agent Bus, operator-surface, SiteOps, and MCP layers.
"""

from runtime.runtime_surfaces.models import (
    RuntimeSurfaceCapability,
    RuntimeSurfaceError,
    RuntimeSurfaceManifest,
)
from runtime.runtime_surfaces.registry import (
    load_runtime_surface_registry,
    load_surface_manifest,
    manifest_root,
    schema_path,
)
from runtime.runtime_surfaces.risk import (
    RiskClassDefinition,
    get_risk_class,
    list_risk_classes,
)
from runtime.runtime_surfaces.policy import (
    CapabilityPolicyRecord,
    build_capability_policy_index,
    capability_policy_records,
)
from runtime.runtime_surfaces.router import (
    RuntimeSurfaceRouteDecision,
    propose_route,
)
from runtime.runtime_surfaces.browser_skill_memory import (
    BrowserSkillMemoryInventory,
    BrowserSkillMemoryRecord,
    normalize_browser_skill_memory,
)
from runtime.runtime_surfaces.audit import (
    append_route_decision,
    read_route_decision_records,
    route_decision_ledger_path,
)
from runtime.runtime_surfaces.inspection import (
    RuntimeSurfaceInspectionError,
    build_runtime_surface_capability_summary,
    build_runtime_surface_summary,
    format_runtime_surface_capability_summary,
    format_runtime_surface_summary,
)
from runtime.runtime_surfaces.review_contract import (
    RuntimeSurfaceRouteReviewError,
    build_route_review_contract,
    format_route_review_contract,
)

__all__ = [
    "RuntimeSurfaceCapability",
    "RuntimeSurfaceError",
    "RuntimeSurfaceManifest",
    "load_runtime_surface_registry",
    "load_surface_manifest",
    "manifest_root",
    "schema_path",
    "RiskClassDefinition",
    "get_risk_class",
    "list_risk_classes",
    "CapabilityPolicyRecord",
    "build_capability_policy_index",
    "capability_policy_records",
    "RuntimeSurfaceRouteDecision",
    "propose_route",
    "BrowserSkillMemoryInventory",
    "BrowserSkillMemoryRecord",
    "normalize_browser_skill_memory",
    "append_route_decision",
    "read_route_decision_records",
    "route_decision_ledger_path",
    "RuntimeSurfaceInspectionError",
    "build_runtime_surface_capability_summary",
    "build_runtime_surface_summary",
    "format_runtime_surface_capability_summary",
    "format_runtime_surface_summary",
    "RuntimeSurfaceRouteReviewError",
    "build_route_review_contract",
    "format_route_review_contract",
]
