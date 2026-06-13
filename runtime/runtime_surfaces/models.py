"""Models and validation for Adaptive Runtime Surface Layer manifests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runtime.runtime_surfaces.risk import VALID_RISK_CLASSES


VALID_STATUS_LABELS: set[str] = {
    "COMPLETE",
    "PARTIAL",
    "PLANNED",
    "NOT BUILT",
    "DOCS-ONLY",
    "VERIFIED",
    "CONFIGURED BUT UNVERIFIED",
    "BLOCKED",
    "DEFERRED",
}

VALID_SURFACE_FAMILIES: set[str] = {
    "provider_model_runtime",
    "agent_runtime",
    "browser_operator",
    "siteops_skill_runtime",
    "runtime_mcp",
    "client_embedded_runtime",
    "filesystem_surface",
    "terminal_surface",
    "desktop_surface",
}

VALID_SURFACE_TYPES: set[str] = {
    "provider_model",
    "agent",
    "browser",
    "siteops_skill",
    "mcp",
    "client_embedded",
    "filesystem",
    "terminal",
    "desktop",
}

VALID_TRUST_CEILINGS: set[str] = {"tier-1", "tier-2", "tier-3", "tier-4"}

REQUIRED_MANIFEST_FIELDS: set[str] = {
    "schema_version",
    "surface_id",
    "display_name",
    "surface_family",
    "surface_type",
    "owner_layer",
    "status",
    "implementation_refs",
    "docs_refs",
    "trust_ceiling",
    "permission_model_refs",
    "gate_operations",
    "capabilities",
    "credential_policy",
    "fallback_policy",
    "writeback_surfaces",
    "audit_targets",
    "routing_policy",
    "mcp_exposure_policy",
}

REQUIRED_CAPABILITY_FIELDS: set[str] = {
    "capability_id",
    "maps_to",
    "risk_class",
    "approval_required",
}


class RuntimeSurfaceError(ValueError):
    """Raised when a runtime surface manifest is invalid or unsafe."""


@dataclass(frozen=True)
class RuntimeSurfaceCapability:
    """A single capability exposed by a runtime surface manifest."""

    capability_id: str
    maps_to: str
    risk_class: str
    approval_required: bool | str
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, surface_id: str, index: int) -> "RuntimeSurfaceCapability":
        if not isinstance(data, dict):
            raise RuntimeSurfaceError(f"{surface_id}.capabilities[{index}] must be an object")
        missing = sorted(REQUIRED_CAPABILITY_FIELDS.difference(data))
        if missing:
            raise RuntimeSurfaceError(f"{surface_id}.capabilities[{index}] missing fields: {missing}")

        capability = cls(
            capability_id=_require_text(data["capability_id"], f"{surface_id}.capabilities[{index}].capability_id"),
            maps_to=_require_text(data["maps_to"], f"{surface_id}.capabilities[{index}].maps_to"),
            risk_class=_require_text(data["risk_class"], f"{surface_id}.capabilities[{index}].risk_class"),
            approval_required=data["approval_required"],
            notes=str(data.get("notes") or ""),
        )
        capability.validate(surface_id=surface_id, index=index)
        return capability

    def validate(self, *, surface_id: str, index: int) -> None:
        if self.risk_class not in VALID_RISK_CLASSES:
            raise RuntimeSurfaceError(
                f"{surface_id}.capabilities[{index}].risk_class {self.risk_class!r} is not valid"
            )
        if self.approval_required not in {True, False, "conditional"}:
            raise RuntimeSurfaceError(
                f"{surface_id}.capabilities[{index}].approval_required must be true, false, or conditional"
            )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "capability_id": self.capability_id,
            "maps_to": self.maps_to,
            "risk_class": self.risk_class,
            "approval_required": self.approval_required,
        }
        if self.notes:
            data["notes"] = self.notes
        return data


@dataclass(frozen=True)
class RuntimeSurfaceManifest:
    """Validated ARSL runtime surface manifest."""

    schema_version: int
    surface_id: str
    display_name: str
    surface_family: str
    surface_type: str
    owner_layer: str
    status: str
    implementation_refs: list[str]
    docs_refs: list[str]
    trust_ceiling: str
    permission_model_refs: list[str]
    gate_operations: list[str]
    capabilities: list[RuntimeSurfaceCapability]
    credential_policy: dict[str, Any]
    fallback_policy: dict[str, Any]
    writeback_surfaces: list[str]
    audit_targets: list[str]
    routing_policy: dict[str, Any]
    mcp_exposure_policy: dict[str, Any]
    source_path: Path | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        source_path: Path | None = None,
        vault_root: str | Path | None = None,
        require_files: bool = True,
    ) -> "RuntimeSurfaceManifest":
        if not isinstance(data, dict):
            raise RuntimeSurfaceError("Runtime surface manifest must be an object")
        missing = sorted(REQUIRED_MANIFEST_FIELDS.difference(data))
        if missing:
            label = source_path.as_posix() if source_path else "manifest"
            raise RuntimeSurfaceError(f"{label} missing fields: {missing}")

        surface_id = _require_text(data["surface_id"], "surface_id")
        capabilities = _require_non_empty_list(data["capabilities"], f"{surface_id}.capabilities")

        manifest = cls(
            schema_version=data["schema_version"],
            surface_id=surface_id,
            display_name=_require_text(data["display_name"], f"{surface_id}.display_name"),
            surface_family=_require_text(data["surface_family"], f"{surface_id}.surface_family"),
            surface_type=_require_text(data["surface_type"], f"{surface_id}.surface_type"),
            owner_layer=_require_text(data["owner_layer"], f"{surface_id}.owner_layer"),
            status=_require_text(data["status"], f"{surface_id}.status"),
            implementation_refs=_require_text_list(data["implementation_refs"], f"{surface_id}.implementation_refs"),
            docs_refs=_require_text_list(data["docs_refs"], f"{surface_id}.docs_refs"),
            trust_ceiling=_require_text(data["trust_ceiling"], f"{surface_id}.trust_ceiling"),
            permission_model_refs=_require_text_list(
                data["permission_model_refs"], f"{surface_id}.permission_model_refs"
            ),
            gate_operations=_require_text_list(data["gate_operations"], f"{surface_id}.gate_operations"),
            capabilities=[
                RuntimeSurfaceCapability.from_dict(capability, surface_id=surface_id, index=index)
                for index, capability in enumerate(capabilities)
            ],
            credential_policy=_require_mapping(data["credential_policy"], f"{surface_id}.credential_policy"),
            fallback_policy=_require_mapping(data["fallback_policy"], f"{surface_id}.fallback_policy"),
            writeback_surfaces=_require_text_list(data["writeback_surfaces"], f"{surface_id}.writeback_surfaces"),
            audit_targets=_require_text_list(data["audit_targets"], f"{surface_id}.audit_targets"),
            routing_policy=_require_mapping(data["routing_policy"], f"{surface_id}.routing_policy"),
            mcp_exposure_policy=_require_mapping(
                data["mcp_exposure_policy"], f"{surface_id}.mcp_exposure_policy"
            ),
            source_path=source_path,
            raw=dict(data),
        )
        manifest.validate(vault_root=vault_root, require_files=require_files)
        return manifest

    def validate(self, *, vault_root: str | Path | None = None, require_files: bool = True) -> None:
        if self.schema_version != 1:
            raise RuntimeSurfaceError(f"{self.surface_id}.schema_version must be 1")
        if self.status not in VALID_STATUS_LABELS:
            raise RuntimeSurfaceError(f"{self.surface_id}.status {self.status!r} is not valid")
        if self.surface_family not in VALID_SURFACE_FAMILIES:
            raise RuntimeSurfaceError(f"{self.surface_id}.surface_family {self.surface_family!r} is not valid")
        if self.surface_type not in VALID_SURFACE_TYPES:
            raise RuntimeSurfaceError(f"{self.surface_id}.surface_type {self.surface_type!r} is not valid")
        if self.trust_ceiling not in VALID_TRUST_CEILINGS:
            raise RuntimeSurfaceError(f"{self.surface_id}.trust_ceiling {self.trust_ceiling!r} is not valid")

        for field_name in (
            "implementation_refs",
            "docs_refs",
            "permission_model_refs",
            "writeback_surfaces",
            "audit_targets",
        ):
            _validate_repo_relative_paths(
                getattr(self, field_name),
                f"{self.surface_id}.{field_name}",
                vault_root=vault_root,
                require_files=require_files and field_name in {"implementation_refs", "docs_refs", "permission_model_refs"},
            )

        _require_policy_booleans(
            self.credential_policy,
            f"{self.surface_id}.credential_policy",
            ("credentials_allowed", "cookies_allowed", "real_profile_allowed"),
        )
        if any(self.credential_policy[key] is True for key in ("credentials_allowed", "cookies_allowed", "real_profile_allowed")):
            raise RuntimeSurfaceError(f"{self.surface_id}.credential_policy cannot grant credential or profile access")

        _require_policy_booleans(self.fallback_policy, f"{self.surface_id}.fallback_policy", ("sticky_fallback_allowed",))
        if self.fallback_policy["sticky_fallback_allowed"] is True:
            raise RuntimeSurfaceError(f"{self.surface_id}.fallback_policy cannot allow sticky fallback")

        if self.routing_policy.get("default") != "deny_unknown":
            raise RuntimeSurfaceError(f"{self.surface_id}.routing_policy.default must be deny_unknown")
        _require_text(self.routing_policy.get("authority_layer"), f"{self.surface_id}.routing_policy.authority_layer")

        _require_policy_booleans(
            self.mcp_exposure_policy,
            f"{self.surface_id}.mcp_exposure_policy",
            ("expose_summary", "expose_raw_manifest"),
        )
        if self.mcp_exposure_policy["expose_raw_manifest"] is True:
            raise RuntimeSurfaceError(f"{self.surface_id}.mcp_exposure_policy cannot expose raw manifests")

    def capability_ids(self) -> set[str]:
        return {capability.capability_id for capability in self.capabilities}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "surface_id": self.surface_id,
            "display_name": self.display_name,
            "surface_family": self.surface_family,
            "surface_type": self.surface_type,
            "owner_layer": self.owner_layer,
            "status": self.status,
            "implementation_refs": list(self.implementation_refs),
            "docs_refs": list(self.docs_refs),
            "trust_ceiling": self.trust_ceiling,
            "permission_model_refs": list(self.permission_model_refs),
            "gate_operations": list(self.gate_operations),
            "capabilities": [capability.to_dict() for capability in self.capabilities],
            "credential_policy": dict(self.credential_policy),
            "fallback_policy": dict(self.fallback_policy),
            "writeback_surfaces": list(self.writeback_surfaces),
            "audit_targets": list(self.audit_targets),
            "routing_policy": dict(self.routing_policy),
            "mcp_exposure_policy": dict(self.mcp_exposure_policy),
        }


def _require_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RuntimeSurfaceError(f"{field_name} is required")
    return text


def _require_non_empty_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise RuntimeSurfaceError(f"{field_name} must be a non-empty list")
    return value


def _require_text_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise RuntimeSurfaceError(f"{field_name} must be a list")
    return [_require_text(item, f"{field_name}[{index}]") for index, item in enumerate(value)]


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeSurfaceError(f"{field_name} must be an object")
    return dict(value)


def _require_policy_booleans(policy: dict[str, Any], field_name: str, keys: tuple[str, ...]) -> None:
    for key in keys:
        if key not in policy:
            raise RuntimeSurfaceError(f"{field_name}.{key} is required")
        if not isinstance(policy[key], bool):
            raise RuntimeSurfaceError(f"{field_name}.{key} must be boolean")


def _validate_repo_relative_paths(
    values: list[str],
    field_name: str,
    *,
    vault_root: str | Path | None,
    require_files: bool,
) -> None:
    root = Path(vault_root).resolve() if vault_root is not None else None
    for value in values:
        path = Path(value)
        if path.is_absolute() or value.startswith(("/", "\\")) or ".." in path.parts or ":" in path.parts[0]:
            raise RuntimeSurfaceError(f"{field_name} must contain repo-relative paths only: {value}")
        if require_files and root is not None and not (root / path).exists():
            raise RuntimeSurfaceError(f"{field_name} path does not exist: {value}")
