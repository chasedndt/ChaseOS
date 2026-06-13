"""ChaseOS Companion Layer v0.1.

Companions are runtime-linked identity profiles for presentation, tone, status
commentary, and governed per-session selection. They are not runtime authority.
"""

from runtime.companion.policy import (
    ALLOWED_EFFECTS,
    FORBIDDEN_EFFECTS,
    INITIAL_COMPANION_IDS,
    SELECTION_TARGET_PATH,
    assert_v0_1_no_authority_change,
    build_authority_report,
)
from runtime.companion.memory import (
    ALLOWED_MEMORY_CLASSES,
    COMPANION_MEMORY_ROOT,
    DENIED_MEMORY_CLASSES,
    MEMORY_POLICY_VERSION,
    build_companion_memory_boundary,
    companion_memory_namespace,
    validate_companion_memory_candidate,
)
from runtime.companion.roster import (
    CORE_COMPANION_METADATA,
    get_companion,
    get_companion_status_metadata,
    list_companions,
)
from runtime.companion.schema import validate_companion_profile
from runtime.companion.selection import (
    get_active_companion,
    preview_companion_switch,
    record_companion_switch,
    select_companion,
)

__all__ = [
    "ALLOWED_EFFECTS",
    "ALLOWED_MEMORY_CLASSES",
    "COMPANION_MEMORY_ROOT",
    "DENIED_MEMORY_CLASSES",
    "FORBIDDEN_EFFECTS",
    "INITIAL_COMPANION_IDS",
    "MEMORY_POLICY_VERSION",
    "SELECTION_TARGET_PATH",
    "CORE_COMPANION_METADATA",
    "assert_v0_1_no_authority_change",
    "build_companion_memory_boundary",
    "build_authority_report",
    "companion_memory_namespace",
    "get_active_companion",
    "get_companion",
    "get_companion_status_metadata",
    "list_companions",
    "preview_companion_switch",
    "record_companion_switch",
    "select_companion",
    "validate_companion_profile",
    "validate_companion_memory_candidate",
]
