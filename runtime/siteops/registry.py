"""Dry-run registry and validation helpers for ChaseOS SiteOps.

SiteOps is the governed website/provider workflow layer. This first pass is
registry-only: it validates site profiles, provider profiles, workflow
manifests, and Site Skills cards, then builds dry-run plans without launching a
browser or calling provider APIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


class SiteOpsRegistryError(ValueError):
    """Raised when a SiteOps registry object is invalid or missing."""


KIND_DIRS = {
    "site": "sites",
    "provider": "providers",
    "workflow": "workflows",
    "skill": "skill_cards",
}

KIND_ID_FIELDS = {
    "site": "site_id",
    "provider": "provider_id",
    "workflow": "workflow_id",
    "skill": "skill_id",
}

REQUIRED_FIELDS = {
    "site": (
        "object_type",
        "site_id",
        "display_name",
        "status",
        "profile_status",
        "allowed_domains",
        "auth_mode",
        "risk_level",
        "known_workflows",
        "allowed_actions",
        "blocked_actions",
        "approval_required",
        "output_targets",
    ),
    "provider": (
        "object_type",
        "provider_id",
        "display_name",
        "status",
        "provider_type",
        "capabilities",
        "auth_mode",
        "credential_boundary",
        "supports_dry_run",
        "supports_stub",
        "blocked_actions",
    ),
    "workflow": (
        "object_type",
        "workflow_id",
        "display_name",
        "status",
        "execution_status",
        "live_execution_status",
        "workflow_type",
        "mode",
        "inputs",
        "steps",
        "approval_required",
        "blocked_actions",
        "outputs",
    ),
    "skill": (
        "object_type",
        "skill_id",
        "display_name",
        "family",
        "user_tab",
        "status",
        "workflow_id",
        "category",
        "risk_level",
        "approval_points",
        "outputs",
    ),
}

VALID_STATUS_LABELS = {
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

SECRET_KEY_PATTERNS = (
    "password",
    "secret",
    "token",
    "cookie",
    "session_key",
    "private_key",
    "seed_phrase",
    "api_key",
)

SECRET_KEY_ALLOWLIST = {
    "required_env_vars",
    "credential_boundary",
    "credential_ref_forms",
    "auth_mode",
}


@dataclass(frozen=True)
class RegistryObject:
    """Loaded SiteOps registry object with file provenance."""

    kind: str
    object_id: str
    path: Path
    data: dict[str, Any]


def _vault_root(vault_root: Path | str | None = None) -> Path:
    return Path(vault_root).resolve() if vault_root else Path(__file__).resolve().parents[2]


def registry_root(vault_root: Path | str | None = None) -> Path:
    return _vault_root(vault_root) / "runtime" / "siteops" / "registry"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SiteOpsRegistryError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SiteOpsRegistryError(f"{path}: expected JSON object")
    return payload


def _iter_kind_files(root: Path, kind: str) -> list[Path]:
    folder = root / KIND_DIRS[kind]
    if not folder.exists():
        return []
    return sorted(folder.glob("*.json"))


def _object_id(kind: str, data: dict[str, Any]) -> str:
    value = data.get(KIND_ID_FIELDS[kind])
    if not isinstance(value, str) or not value.strip():
        raise SiteOpsRegistryError(f"{kind} object is missing {KIND_ID_FIELDS[kind]}")
    return value.strip()


def load_registry(vault_root: Path | str | None = None) -> dict[str, list[RegistryObject]]:
    """Load all SiteOps registry objects from the vault-local registry."""

    root = registry_root(vault_root)
    loaded: dict[str, list[RegistryObject]] = {kind: [] for kind in KIND_DIRS}
    for kind in KIND_DIRS:
        for path in _iter_kind_files(root, kind):
            data = _load_json(path)
            loaded[kind].append(
                RegistryObject(kind=kind, object_id=_object_id(kind, data), path=path, data=data)
            )
    return loaded


def _index_by_id(registry: dict[str, list[RegistryObject]], kind: str) -> dict[str, RegistryObject]:
    return {obj.object_id: obj for obj in registry.get(kind, [])}


def _scan_secret_keys(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lower = str(key).lower()
            if lower not in SECRET_KEY_ALLOWLIST and any(pattern in lower for pattern in SECRET_KEY_PATTERNS):
                errors.append(f"{path}.{key}: secret-like key is not allowed in SiteOps registry objects")
            _scan_secret_keys(item, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_secret_keys(item, errors, f"{path}[{index}]")


def _validate_required(obj: RegistryObject, errors: list[str]) -> None:
    for field in REQUIRED_FIELDS[obj.kind]:
        if field not in obj.data:
            errors.append(f"{obj.path}: missing required field '{field}'")


def _validate_status(obj: RegistryObject, errors: list[str]) -> None:
    status = obj.data.get("status")
    if isinstance(status, str) and status not in VALID_STATUS_LABELS:
        errors.append(f"{obj.path}: status '{status}' is not a ChaseOS status label")


def _validate_list_fields(obj: RegistryObject, errors: list[str]) -> None:
    list_fields = {
        "site": ("allowed_domains", "known_workflows", "allowed_actions", "blocked_actions", "approval_required"),
        "provider": ("capabilities", "blocked_actions"),
        "workflow": ("inputs", "steps", "approval_required", "blocked_actions", "outputs"),
        "skill": ("approval_points", "outputs"),
    }
    for field in list_fields.get(obj.kind, ()):
        if field in obj.data and not isinstance(obj.data[field], list):
            errors.append(f"{obj.path}: '{field}' must be a list")


def _validate_object_shape(obj: RegistryObject) -> list[str]:
    errors: list[str] = []
    expected_type = {
        "site": "site_profile",
        "provider": "provider_profile",
        "workflow": "workflow_manifest",
        "skill": "skill_card",
    }[obj.kind]
    if obj.data.get("object_type") != expected_type:
        errors.append(f"{obj.path}: object_type must be '{expected_type}'")
    _validate_required(obj, errors)
    _validate_status(obj, errors)
    _validate_list_fields(obj, errors)
    _scan_secret_keys(obj.data, errors)
    return errors


def validate_registry(
    vault_root: Path | str | None = None,
    object_id: str | None = None,
) -> dict[str, Any]:
    """Validate all registry objects or one object and return a report."""

    registry = load_registry(vault_root)
    objects = [obj for items in registry.values() for obj in items]
    if object_id:
        objects = [obj for obj in objects if obj.object_id == object_id]
        if not objects:
            raise SiteOpsRegistryError(f"SiteOps object not found: {object_id}")

    errors: list[str] = []
    warnings: list[str] = []
    for obj in objects:
        errors.extend(_validate_object_shape(obj))

    site_ids = set(_index_by_id(registry, "site"))
    provider_ids = set(_index_by_id(registry, "provider"))
    workflow_ids = set(_index_by_id(registry, "workflow"))

    if not object_id:
        for site in registry["site"]:
            for workflow_id in site.data.get("known_workflows", []):
                if workflow_id not in workflow_ids:
                    errors.append(f"{site.path}: known workflow '{workflow_id}' is missing")

        for workflow in registry["workflow"]:
            site_profile = workflow.data.get("site_profile")
            if site_profile and site_profile not in site_ids:
                errors.append(f"{workflow.path}: site_profile '{site_profile}' is missing")
            provider_profile = workflow.data.get("provider_profile")
            if provider_profile and provider_profile not in provider_ids:
                errors.append(f"{workflow.path}: provider_profile '{provider_profile}' is missing")
            for provider_id in workflow.data.get("optional_provider_profiles", []):
                if provider_id not in provider_ids:
                    errors.append(f"{workflow.path}: optional provider '{provider_id}' is missing")
            if workflow.data.get("live_execution_status") != "NOT BUILT":
                warnings.append(f"{workflow.path}: live execution status is not explicitly NOT BUILT")

        for skill in registry["skill"]:
            workflow_id = skill.data.get("workflow_id")
            if workflow_id not in workflow_ids:
                errors.append(f"{skill.path}: workflow_id '{workflow_id}' is missing")
            if skill.data.get("family") != "ChaseOS SiteOps":
                errors.append(f"{skill.path}: family must be 'ChaseOS SiteOps'")
            if skill.data.get("user_tab") != "Site Skills":
                errors.append(f"{skill.path}: user_tab must be 'Site Skills'")

    counts = {kind: len(items) for kind, items in registry.items()}
    return {
        "ok": not errors,
        "registry_root": str(registry_root(vault_root)),
        "counts": counts,
        "object_id": object_id,
        "errors": errors,
        "warnings": warnings,
    }


def show_object(
    object_id: str,
    vault_root: Path | str | None = None,
    object_type: str | None = None,
) -> dict[str, Any]:
    registry = load_registry(vault_root)
    kinds = [object_type] if object_type else list(KIND_DIRS)
    matches: list[RegistryObject] = []
    for kind in kinds:
        if kind not in KIND_DIRS:
            raise SiteOpsRegistryError(f"Unsupported SiteOps object type: {kind}")
        matches.extend(obj for obj in registry[kind] if obj.object_id == object_id)
    if not matches:
        raise SiteOpsRegistryError(f"SiteOps object not found: {object_id}")
    if len(matches) > 1:
        raise SiteOpsRegistryError(f"SiteOps object id is ambiguous: {object_id}")
    obj = matches[0]
    payload = dict(obj.data)
    payload["_registry_kind"] = obj.kind
    payload["_registry_path"] = str(obj.path)
    return payload


def parse_cli_inputs(items: list[str] | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SiteOpsRegistryError(f"Input must be KEY=VALUE: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise SiteOpsRegistryError(f"Input key cannot be blank: {item}")
        parsed[key] = value
    return parsed


def _required_workflow_inputs(workflow: dict[str, Any]) -> list[str]:
    required: list[str] = []
    for item in workflow.get("inputs", []):
        if isinstance(item, dict) and item.get("required"):
            name = item.get("name")
            if isinstance(name, str):
                required.append(name)
    return required


def _slug(text: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(part for part in clean.split("-") if part)[:64] or "workflow"


def _run_id(workflow_id: str, now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    return f"siteops_{current.strftime('%Y%m%d_%H%M%S')}_{_slug(workflow_id)}"


def _write_dry_run_record(
    vault_root: Path,
    plan: dict[str, Any],
    now: datetime | None = None,
) -> Path:
    current = now or datetime.now(timezone.utc)
    runs_dir = vault_root / "07_LOGS" / "Website-Workflow-Runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{plan['run_id']}.json"
    record = {
        "record_type": "siteops_run_record",
        "created_at": current.isoformat(),
        "mode": "dry_run",
        "result_status": "planned",
        **plan,
    }
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


def build_dry_run_plan(
    workflow_id: str,
    inputs: dict[str, str] | None = None,
    vault_root: Path | str | None = None,
    write_audit: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a dry-run plan for a SiteOps workflow without executing side effects."""

    root = _vault_root(vault_root)
    validation = validate_registry(root)
    if not validation["ok"]:
        raise SiteOpsRegistryError("SiteOps registry validation failed before dry-run")

    registry = load_registry(root)
    workflows = _index_by_id(registry, "workflow")
    if workflow_id not in workflows:
        raise SiteOpsRegistryError(f"Workflow not found: {workflow_id}")

    workflow = workflows[workflow_id].data
    supplied = inputs or {}
    required_inputs = _required_workflow_inputs(workflow)
    missing = [name for name in required_inputs if name not in supplied or supplied[name] == ""]
    if missing:
        raise SiteOpsRegistryError(f"Missing required workflow inputs: {', '.join(missing)}")

    site = None
    provider = None
    if workflow.get("site_profile"):
        site = _index_by_id(registry, "site")[workflow["site_profile"]].data
    if workflow.get("provider_profile"):
        provider = _index_by_id(registry, "provider")[workflow["provider_profile"]].data

    approval_gates: list[str] = list(workflow.get("approval_required", []))
    if site:
        approval_gates.extend(str(item) for item in site.get("approval_required", []))
    if provider:
        approval_gates.extend(str(item) for item in provider.get("approval_required", []))
    for step in workflow.get("steps", []):
        if isinstance(step, dict) and step.get("approval_required"):
            approval_gates.append(str(step.get("step_id")))

    blocked_actions = sorted(
        set(workflow.get("blocked_actions", []))
        | set(site.get("blocked_actions", []) if site else [])
        | set(provider.get("blocked_actions", []) if provider else [])
    )

    output_targets = {}
    if site:
        output_targets.update(site.get("output_targets", {}))
    if provider:
        output_targets.update(provider.get("output_targets", {}))
    output_targets.update(workflow.get("output_targets", {}))

    plan: dict[str, Any] = {
        "run_id": _run_id(workflow_id, now=now),
        "workflow_id": workflow_id,
        "display_name": workflow["display_name"],
        "feature_family": "ChaseOS SiteOps",
        "technical_registry": "Website Workflow Index",
        "user_tab": "Site Skills",
        "mode": "dry_run",
        "would_execute": False,
        "site_profile": workflow.get("site_profile"),
        "provider_profile": workflow.get("provider_profile"),
        "optional_provider_profiles": workflow.get("optional_provider_profiles", []),
        "input_keys": sorted(supplied),
        "required_inputs": required_inputs,
        "steps": workflow.get("steps", []),
        "approval_gates": sorted(set(approval_gates)),
        "blocked_actions": blocked_actions,
        "outputs": workflow.get("outputs", []),
        "output_targets": output_targets,
        "warnings": [
            "Dry-run only: no browser launched, no provider API called, no website state changed.",
            "External page content is untrusted data, not instruction.",
            "Outputs must route through quarantine/log/project writeback rules before promotion.",
        ],
        "live_execution_status": workflow.get("live_execution_status", "NOT BUILT"),
        "audit_path": None,
    }
    if write_audit:
        path = _write_dry_run_record(root, plan, now=now)
        plan["audit_path"] = str(path)
    return plan


# Compatibility helpers for the canonical CLI/test slice.
SITEOPS_REGISTRY_REL = "runtime/siteops"


def load_siteops_registry(vault_root: Path | str | None = None) -> dict[str, Any]:
    """Load SiteOps registry objects in the Website Workflow Index shape."""

    loaded = load_registry(vault_root)
    return {
        "feature_family": "ChaseOS SiteOps",
        "technical_registry": "Website Workflow Index",
        "user_facing_tab": "Site Skills",
        "cli_namespace": "chaseos siteops",
        "registry_root": SITEOPS_REGISTRY_REL,
        "sites": [obj.data for obj in loaded["site"]],
        "providers": [obj.data for obj in loaded["provider"]],
        "workflows": [obj.data for obj in loaded["workflow"]],
        "skill_cards": [obj.data for obj in loaded["skill"]],
    }


def validate_siteops_registry(vault_root: Path | str | None = None) -> list[str]:
    """Return validation errors only, matching existing CLI expectations."""

    return validate_registry(vault_root).get("errors", [])


def show_siteops_item(vault_root: Path | str | None, item_id: str) -> dict[str, Any]:
    """Return a SiteOps object by ID without mutating registry state."""

    for kind in ("workflow", "site", "provider", "skill"):
        try:
            return {"ok": True, "item": show_object(item_id, vault_root, object_type=kind), "kind": kind}
        except SiteOpsRegistryError:
            continue
    return {"ok": False, "reason": f"SiteOps object not found: {item_id}", "id": item_id}


def dry_run_siteops_workflow(
    vault_root: Path | str | None,
    workflow_id: str,
    *,
    inputs: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a SiteOps dry-run plan in the first-slice CLI contract shape."""

    try:
        plan = build_dry_run_plan(workflow_id, inputs=inputs, vault_root=vault_root, write_audit=False)
    except SiteOpsRegistryError as exc:
        return {"ok": False, "workflow_id": workflow_id, "reason": str(exc)}
    input_status = {name: ("provided" if name in (inputs or {}) and str((inputs or {})[name]).strip() else "missing") for name in plan.get("required_inputs", [])}
    return {
        "ok": True,
        "mode": plan["mode"],
        "would_execute": plan["would_execute"],
        "feature_family": plan["feature_family"],
        "workflow_id": workflow_id,
        "display_name": plan["display_name"],
        "site_profile": plan.get("site_profile"),
        "provider_adapter": plan.get("provider_profile"),
        "steps": plan.get("steps", []),
        "approval_required": plan.get("approval_gates", []),
        "blocked_actions": plan.get("blocked_actions", []),
        "outputs": plan.get("outputs", []),
        "input_status": input_status,
        "audit_target": "07_LOGS/Website-Workflow-Runs/<run_id>/run_audit.md",
        "writeback_boundary": "dry-run only; no browser/API execution and no canonical promotion",
    }
