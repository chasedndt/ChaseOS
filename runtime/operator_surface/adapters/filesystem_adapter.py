"""
runtime.operator_surface.adapters.filesystem_adapter

Filesystem Operator Surface Adapter — STUB

Status: STUB — formally represented; not yet implemented.
This stub ensures architecture is not browser-locked.
Implementation is a future Phase 9 sibling surface target.

See: 06_AGENTS/Full-System-Operator-Surface.md Section 8.4

NOTE: The Filesystem Operator Surface handles general cross-directory file operations
that fall outside the capture path. It does NOT replace runtime/capture/ (which handles
vault-to-quarantine writes) or the ChaseOS Gate (which governs vault canonical writes).
"""

from __future__ import annotations

from typing import Callable

from runtime.operator_surface.adapters.base import OperatorSurfaceAdapterBase
from runtime.operator_surface.capabilities import OperatorCapability, SurfaceType, GroundingMode
from runtime.operator_surface.contracts import OperatorScope, OperatorSession, StepResult, RecoveryResult
from runtime.operator_surface.events import OperatorEvent


class FilesystemAdapter(OperatorSurfaceAdapterBase):
    """
    STUB — Filesystem Operator Surface Adapter.

    Not yet implemented. Class is registered to formally represent the surface.

    Future implementation will provide:
    - Explicit allowed path prefix enforcement
    - Operation classification (read / write / delete / move)
    - Delete operations always require approval gate
    - Cross-path validation (both paths must be in allowed_paths)
    - Integration with vault Gate for writes to ChaseOS vault paths

    Key rule: DELETE always requires approval gate — no exceptions.
    Key rule: Cross-repo file operations require both source and target in allowed_paths.
    """

    ADAPTER_ID = "filesystem-pathlib-v1"
    SURFACE_TYPE = SurfaceType.FILESYSTEM
    ADAPTER_VERSION = "0.0.1"
    ADAPTER_STATUS = "stub"
    DESCRIPTION = "Filesystem Operator Surface via Python pathlib — STUB"
    CAPABILITIES = frozenset({
        OperatorCapability.FILESYSTEM_READ,
        OperatorCapability.FILESYSTEM_WRITE,
        OperatorCapability.FILESYSTEM_LIST,
        OperatorCapability.FILESYSTEM_MOVE,
        OperatorCapability.FILESYSTEM_DELETE,
    })
    REQUIRED_SCOPE_FIELDS = frozenset({"allowed_paths"})
    FORBIDDEN_SCOPE_PROPERTIES = frozenset({"credential_access"})
    MIN_TRUST_TIER = 2
    APPROVAL_REQUIRED_ACTIONS = frozenset({
        "file_delete",      # always — no exceptions
        "file_write",
        "file_move",
        "cross_repo_copy",
    })
    GROUNDING_MODES = []  # Filesystem: no visual grounding needed

    def initialize(self, scope: OperatorScope, session: OperatorSession) -> None:
        raise NotImplementedError("FilesystemAdapter is a STUB — not yet implemented.")

    def plan(self, goal: str, context: dict) -> list[dict]:
        raise NotImplementedError("FilesystemAdapter is a STUB — not yet implemented.")

    def execute_step(self, step: dict, emit_event: Callable[[OperatorEvent], None]) -> StepResult:
        raise NotImplementedError("FilesystemAdapter is a STUB — not yet implemented.")

    def recover(self, failed_step: dict, emit_event: Callable[[OperatorEvent], None]) -> RecoveryResult:
        raise NotImplementedError("FilesystemAdapter is a STUB — not yet implemented.")

    def teardown(self, outcome: str, emit_event: Callable[[OperatorEvent], None]) -> None:
        pass  # STUB — nothing to tear down

    def build_audit_payload(self) -> dict:
        return {
            "adapter_id": self.ADAPTER_ID,
            "surface_type": self.SURFACE_TYPE.value,
            "adapter_status": "stub",
            "implementation_note": "STUB — not yet implemented.",
        }
