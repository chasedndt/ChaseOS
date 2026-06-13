"""
runtime.operator_surface.adapters.desktop_adapter

Desktop / Window Operator Surface Adapter — STUB

Status: STUB — formally represented; not yet implemented.
This stub ensures architecture is not browser-locked.
Implementation is a future Phase 9/10 sibling surface target.

See: 06_AGENTS/Full-System-Operator-Surface.md Section 8.3
"""

from __future__ import annotations

from typing import Callable

from runtime.operator_surface.adapters.base import OperatorSurfaceAdapterBase
from runtime.operator_surface.capabilities import OperatorCapability, SurfaceType, GroundingMode
from runtime.operator_surface.contracts import OperatorScope, OperatorSession, StepResult, RecoveryResult
from runtime.operator_surface.events import OperatorEvent


class DesktopAdapter(OperatorSurfaceAdapterBase):
    """
    STUB — Desktop / Window Operator Surface Adapter.

    Not yet implemented. Class is registered to formally represent the surface
    and prevent architecture drift to browser-only assumptions.

    Future implementation will provide:
    - Accessibility API integration (Windows UI Automation / macOS Accessibility API)
    - Window/process targeting
    - Visual grounding (screenshot + element detection)
    - Mouse/keyboard action model
    - Application lifecycle management

    Note: Desktop is a higher-risk surface — actions are harder to scope and reverse.
    More conservative approval model required compared to browser or terminal.
    """

    ADAPTER_ID = "desktop-accessibility-v1"
    SURFACE_TYPE = SurfaceType.DESKTOP
    ADAPTER_VERSION = "0.0.1"
    ADAPTER_STATUS = "stub"
    DESCRIPTION = "Desktop Window Operator Surface via Accessibility API — STUB"
    CAPABILITIES = frozenset({
        OperatorCapability.DESKTOP_READ,
        OperatorCapability.DESKTOP_CLICK,
        OperatorCapability.DESKTOP_TYPE,
        OperatorCapability.DESKTOP_WINDOW_MANAGE,
    })
    REQUIRED_SCOPE_FIELDS = frozenset({"target_uris"})  # target_uris = target process/window names
    FORBIDDEN_SCOPE_PROPERTIES = frozenset({"credential_access"})
    MIN_TRUST_TIER = 2
    APPROVAL_REQUIRED_ACTIONS = frozenset({
        "write_action",
        "window_close",
        "application_launch",
        "key_sequence",           # keyboard shortcuts that could have broad effects
    })
    GROUNDING_MODES = [
        GroundingMode.ACCESSIBILITY,
        GroundingMode.VISUAL_SCREENSHOT,
    ]

    def initialize(self, scope: OperatorScope, session: OperatorSession) -> None:
        raise NotImplementedError("DesktopAdapter is a STUB — not yet implemented.")

    def plan(self, goal: str, context: dict) -> list[dict]:
        raise NotImplementedError("DesktopAdapter is a STUB — not yet implemented.")

    def execute_step(self, step: dict, emit_event: Callable[[OperatorEvent], None]) -> StepResult:
        raise NotImplementedError("DesktopAdapter is a STUB — not yet implemented.")

    def recover(self, failed_step: dict, emit_event: Callable[[OperatorEvent], None]) -> RecoveryResult:
        raise NotImplementedError("DesktopAdapter is a STUB — not yet implemented.")

    def teardown(self, outcome: str, emit_event: Callable[[OperatorEvent], None]) -> None:
        pass  # STUB — nothing to tear down

    def build_audit_payload(self) -> dict:
        return {
            "adapter_id": self.ADAPTER_ID,
            "surface_type": self.SURFACE_TYPE.value,
            "adapter_status": "stub",
            "implementation_note": "STUB — not yet implemented.",
        }
