"""
runtime.operator_surface.adapter_registry

Registry for FSOS surface adapters.
AOR uses the registry to look up which adapter handles a given SurfaceType.

Adapters are registered by class, not instance.
Instantiation happens per-run inside the executor.

Architecture: 06_AGENTS/Operator-Surface-Adapter-Spec.md Section 13
"""

from __future__ import annotations

from typing import Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.operator_surface.adapters.base import OperatorSurfaceAdapterBase

from runtime.operator_surface.capabilities import SurfaceType


class AdapterNotFound(Exception):
    """Raised when no adapter is registered for the requested SurfaceType."""
    pass


class AdapterRegistry:
    """
    Singleton-friendly registry of FSOS surface adapter classes.
    Keyed by SurfaceType.

    Only one adapter class may be registered per surface type.
    To replace an adapter, call register() with replace=True.
    """

    def __init__(self):
        self._registry: dict[SurfaceType, Type] = {}

    def register(self, adapter_class: Type, replace: bool = False) -> None:
        """
        Register an adapter class.
        adapter_class must have SURFACE_TYPE and ADAPTER_STATUS class attributes.
        """
        if not hasattr(adapter_class, "SURFACE_TYPE"):
            raise ValueError(
                f"Adapter class {adapter_class.__name__} missing SURFACE_TYPE class attribute."
            )
        surface_type = adapter_class.SURFACE_TYPE
        if surface_type in self._registry and not replace:
            raise ValueError(
                f"Adapter for surface '{surface_type}' already registered "
                f"({self._registry[surface_type].__name__}). Use replace=True to override."
            )
        self._registry[surface_type] = adapter_class

    def get_by_surface(self, surface: SurfaceType) -> Type:
        """
        Return the registered adapter class for this surface type.
        Raises AdapterNotFound if no adapter is registered.
        """
        if surface not in self._registry:
            raise AdapterNotFound(
                f"No adapter registered for surface '{surface}'. "
                f"Registered surfaces: {list(self._registry.keys())}"
            )
        return self._registry[surface]

    def list_registered(self) -> dict[str, dict]:
        """Return a summary of all registered adapters."""
        result = {}
        for surface_type, cls in self._registry.items():
            result[surface_type.value] = {
                "adapter_id": getattr(cls, "ADAPTER_ID", "unknown"),
                "adapter_version": getattr(cls, "ADAPTER_VERSION", "unknown"),
                "adapter_status": getattr(cls, "ADAPTER_STATUS", "unknown"),
                "description": getattr(cls, "DESCRIPTION", ""),
            }
        return result

    def is_registered(self, surface: SurfaceType) -> bool:
        return surface in self._registry


# Module-level default registry — populated by importing adapters
_default_registry = AdapterRegistry()


def get_default_registry() -> AdapterRegistry:
    return _default_registry
