#!/usr/bin/env python3
"""
chaseos_gate.py — ChaseOS Gate Entrypoint (Stub)

This is the starter Gate entrypoint. It provides:
- Adapter manifest loading and validation
- Policy check interface (can be imported by hook scripts)
- Task profile loading

This is a Phase 6 preflight stub. Full runtime enforcement is Phase 7/8.

Current capabilities:
    - load_adapter_manifest(adapter_id) -> dict
    - load_task_profile(task_type) -> dict
    - check_write_permission(adapter_id, write_target) -> (bool, str)
    - check_task_type(adapter_id, task_type) -> (bool, str)
    - check_gateway_write_target(category, write_target) -> (bool, str)
    - check_external_api(api_id) -> (bool, str)
    - check_control_plane_transport(transport) -> (bool, str)
    - check_credential_reference(kind, target) -> (bool, str)
    - check_coordination_path(adapter_id, coordination_sensitive, via_bus, target_runtime=None) -> (bool, str)
    - validate_manifest(manifest) -> list[str]  # returns list of validation errors

Architecture: 06_AGENTS/ChaseOS-Gate.md
Manifest standard: 06_AGENTS/Adapter-Manifest-Standard.md
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


# Vault root is two levels up from this file (runtime/chaseos_gate.py)
VAULT_ROOT = Path(__file__).parent.parent
POLICY_DIR = VAULT_ROOT / "runtime" / "policy"
ADAPTERS_DIR = POLICY_DIR / "adapters"
TASKS_DIR = POLICY_DIR / "tasks"
PROTECTED_FILES_PATH = POLICY_DIR / "protected_files.yaml"
GATEWAY_ALLOWLISTS_PATH = POLICY_DIR / "gateway_allowlists.json"

# Required fields per Adapter-Manifest-Standard.md
REQUIRED_MANIFEST_FIELDS = [
    "adapter_id",
    "adapter_name",
    "provider",
    "surface",
    "adapter_class",
    "status",
    "trust_ceiling",
    "markdown_doc",
    "allowed_write_targets",
    "protected_file_behavior",
    "promotion_behavior",
    "external_side_effect_policy",
    "coordination_policy",
    "approval_mode",
    "audit_log_target",
]

SUPPORT_POLICY_FIELDS = {
    "config_id",
    "registry_id",
}

RUNTIME_PROVIDER_LIVE_PROBE_OPERATION = "runtime.provider.live_probe"
RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID = "rpgl.live_provider_probe.v1"
RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_REQUIRED_FIELDS = (
    "operator_request_id",
    "gate_approval_id",
    "provider_id",
    "model",
    "runtime",
    "probe_scope",
    "external_api_id",
    "timeout_policy",
    "secret_reference_metadata_only",
)
RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION = "runtime.provider.config_apply"
RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID = "rpgl.provider_config_apply.v1"
RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_REQUIRED_FIELDS = (
    "operator_request_id",
    "gate_approval_id",
    "proposal_id",
    "queue_item_id",
    "expected_primary_model",
    "proposed_changes_digest_sha256",
    "target_paths",
    "rollback_plan",
    "post_apply_verification",
    "files_modified_expected",
)
BROWSER_CDP_READ_ONLY_PROOF_OPERATION = "browser.cdp.read_only_proof"
BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID = "bosl.cdp_read_only_proof.v1"
BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_REQUIRED_FIELDS = (
    "operator_request_id",
    "gate_approval_id",
    "runtime",
    "target_url",
    "allowed_domains",
    "cdp_endpoint",
    "launch_strategy",
    "browser_profile_policy",
    "allowed_actions",
    "artifact_targets",
    "screenshot_retention",
    "secret_policy",
)


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------


def _coerce_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def _parse_simple_yaml(text: str) -> dict:
    result: dict[str, Any] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if not line.startswith(" ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                nested: dict[str, Any] = {}
                items: list[str] = []
                i += 1
                while i < len(lines):
                    child = lines[i].rstrip()
                    child_stripped = child.strip()
                    if not child_stripped or child_stripped.startswith("#"):
                        i += 1
                        continue
                    if not child.startswith("  "):
                        break
                    if child_stripped.startswith("- "):
                        items.append(child_stripped[2:].strip().strip('"'))
                        i += 1
                        continue
                    if ":" in child_stripped:
                        subkey, subvalue = child_stripped.split(":", 1)
                        nested[subkey.strip()] = _coerce_scalar(subvalue.strip())
                    i += 1
                result[key] = items if items and not nested else nested
                continue
            result[key] = _coerce_scalar(value)
        i += 1
    return result


def _load_yaml(path: Path) -> dict:
    """Load a YAML file. Returns empty dict on error."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {}
    return _parse_simple_yaml(text) or {}


def load_adapter_manifest(adapter_id: str) -> dict:
    """Load the adapter manifest for the given adapter_id.

    Args:
        adapter_id: The adapter ID.

    Returns:
        Manifest dict, or empty dict if not found.

    Notes:
        The primary resolution path is filename-based (`runtime/policy/adapters/[stem].yaml`).
        For historical manifests whose filename and `adapter_id` differ, fall back to
        scanning all manifests and matching the declared `adapter_id` field.
    """
    manifest_path = ADAPTERS_DIR / f"{adapter_id}.yaml"
    if manifest_path.exists():
        return _load_yaml(manifest_path)

    for manifest in load_all_manifests().values():
        if manifest.get("adapter_id") == adapter_id:
            return manifest

    return {}


def load_all_manifests() -> dict[str, dict]:
    """Load all adapter manifests from runtime/policy/adapters/."""
    manifests = {}
    if not ADAPTERS_DIR.exists():
        return manifests
    for yaml_file in ADAPTERS_DIR.glob("*.yaml"):
        adapter_id = yaml_file.stem
        manifest = _load_yaml(yaml_file)
        if is_support_policy_file(manifest):
            continue
        manifests[adapter_id] = manifest
    return manifests


def is_support_policy_file(manifest: dict) -> bool:
    """Return True for adapter-adjacent config/registry files, not manifests."""
    return any(field in manifest for field in SUPPORT_POLICY_FIELDS)


def load_task_profile(task_type: str) -> dict:
    """Load the task profile for the given task_type.

    Args:
        task_type: The task type slug (matches filename in runtime/policy/tasks/)

    Returns:
        Task profile dict, or empty dict if not found.
    """
    profile_path = TASKS_DIR / f"{task_type}.yaml"
    return _load_yaml(profile_path)


def load_protected_files() -> list[str]:
    """Load the protected files list."""
    data = _load_yaml(PROTECTED_FILES_PATH)
    return data.get("protected_files", [])


def load_gateway_allowlists() -> dict:
    """Load explicit Gate/Gateway allowlists.

    The allowlist file is intentionally JSON so it remains parseable without
    PyYAML. Missing or malformed allowlists fail closed in check helpers.
    """
    if not GATEWAY_ALLOWLISTS_PATH.exists():
        return {}
    try:
        return json.loads(GATEWAY_ALLOWLISTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _normalize_gate_path(write_target: str) -> str:
    path = Path(str(write_target))
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(VAULT_ROOT.resolve())
        except ValueError:
            return str(path).replace("\\", "/")
    normalized = str(path).replace("\\", "/").lstrip("./")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized.rstrip("/") if normalized != "/" else normalized


def _matches_allowlist_pattern(value: str, patterns: list[str]) -> bool:
    normalized = _normalize_gate_path(value)
    if normalized.startswith("../") or "/../" in normalized or normalized == "..":
        return False
    for pattern in patterns:
        normalized_pattern = str(pattern).replace("\\", "/").lstrip("./")
        if normalized_pattern.endswith("/**") and normalized == normalized_pattern[:-3].rstrip("/"):
            return True
        if fnmatch.fnmatch(normalized, normalized_pattern):
            return True
    return False


def check_gateway_write_target(category: str, write_target: str) -> tuple[bool, str]:
    """Check a write target against the explicit gateway write-target allowlist."""
    allowlists = load_gateway_allowlists()
    patterns = (allowlists.get("write_targets") or {}).get(category)
    if not isinstance(patterns, list) or not patterns:
        return False, f"Write target category '{category}' is not allowlisted."
    if _matches_allowlist_pattern(write_target, [str(pattern) for pattern in patterns]):
        return True, f"write target allowed by category '{category}'"
    return False, f"Write target '{write_target}' is outside allowlisted category '{category}'."


def check_external_api(api_id: str) -> tuple[bool, str]:
    """Check an external API identifier against the explicit gateway allowlist."""
    allowlists = load_gateway_allowlists()
    external_apis = allowlists.get("external_apis") or {}
    if api_id in external_apis:
        return True, f"external API '{api_id}' is allowlisted"
    return False, f"External API '{api_id}' is not allowlisted."


def check_control_plane_transport(transport: str) -> tuple[bool, str]:
    """Check a control-plane transport against the explicit gateway allowlist."""
    allowlists = load_gateway_allowlists()
    transports = allowlists.get("control_plane_transports") or {}
    if transport in transports:
        return True, f"control-plane transport '{transport}' is allowlisted"
    return False, f"Control-plane transport '{transport}' is not allowlisted."


def _credential_reference_policy() -> dict:
    allowlists = load_gateway_allowlists()
    return allowlists.get("credential_references") or {}


def check_credential_reference(kind: str | None, target: str | None) -> tuple[bool, str]:
    """Validate that a credential field stores a reference, never a secret value."""
    policy = _credential_reference_policy()
    allowed_kinds = set(policy.get("allowed_kinds") or [])
    if not kind or str(kind) not in allowed_kinds:
        return False, f"Credential reference kind is not allowlisted: {kind!r}"
    if not target or not str(target).strip():
        return False, "Credential reference target is missing."

    target_text = str(target).strip()
    for pattern in policy.get("allowed_target_patterns") or []:
        regex = pattern.get("regex") if isinstance(pattern, dict) else None
        if regex and re.fullmatch(regex, target_text):
            return True, "credential reference target allowed"

    return (
        False,
        "Credential reference target must be an env var name, keychain URI, or template placeholder.",
    )


_SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"ya29\.[0-9A-Za-z_-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{20,}", re.IGNORECASE),
)


def _looks_like_secret_value(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    if any(pattern.search(text) for pattern in _SECRET_VALUE_PATTERNS):
        return True
    compact = text.replace("-", "").replace("_", "").replace("=", "")
    return (
        len(text) >= 40
        and len(text.split()) == 1
        and any(char.isdigit() for char in compact)
        and any(char.isalpha() for char in compact)
    )


def _is_reference_state_key(key: str) -> bool:
    policy = _credential_reference_policy()
    allowed_keys = set(policy.get("reference_only_state_keys") or [])
    return key.lower() in allowed_keys


def _is_secret_value_state_key(key: str) -> bool:
    lower = key.lower()
    if lower.endswith("_present") or lower.endswith("_kind"):
        return False
    if _is_reference_state_key(lower):
        return False
    policy = _credential_reference_policy()
    fragments = policy.get("secret_value_key_fragments") or []
    return any(str(fragment) in lower for fragment in fragments)


def find_credential_boundary_violations(payload: Any, prefix: str = "state") -> list[str]:
    """Return secret-boundary violations for setup/gateway state payloads.

    Setup and gateway commands may persist env var names, keychain references,
    and template placeholders. They must never persist raw secret values.
    """
    violations: list[str] = []

    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            lower = key_text.lower()

            if lower in {"secret_reference_kind", "credential_reference_kind"} and value is not None:
                allowed_kinds = set(_credential_reference_policy().get("allowed_kinds") or [])
                if str(value) not in allowed_kinds:
                    violations.append(f"{key_path}: credential reference kind is not allowlisted")

            if _is_reference_state_key(lower) and value is not None:
                sibling_kind = (
                    payload.get("secret_reference_kind")
                    or payload.get("credential_reference_kind")
                    or "template-placeholder"
                )
                allowed, reason = check_credential_reference(str(sibling_kind), str(value))
                if not allowed:
                    violations.append(f"{key_path}: {reason}")

            if isinstance(value, str):
                if _is_secret_value_state_key(key_text):
                    violations.append(
                        f"{key_path}: secret-bearing fields must store references, not values"
                    )
                elif _looks_like_secret_value(value):
                    violations.append(f"{key_path}: value looks like a raw secret")

            violations.extend(find_credential_boundary_violations(value, key_path))

    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            violations.extend(find_credential_boundary_violations(item, f"{prefix}[{index}]"))

    return violations


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_manifest(manifest: dict) -> list[str]:
    """Validate a manifest against the required fields schema.

    Returns:
        List of validation error strings. Empty list means valid.
    """
    errors = []
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")

    allowlists = load_gateway_allowlists()
    allowed_global_task_types = set(allowlists.get("task_types") or [])
    for task_type in manifest.get("allowed_task_types", []):
        if task_type not in allowed_global_task_types:
            errors.append(f"allowed_task_types contains non-allowlisted task type: {task_type}")

    allowlisted_write_categories = set((allowlists.get("write_targets") or {}).keys())
    for category, enabled in (manifest.get("allowed_write_targets") or {}).items():
        if enabled is True and category != "protected_files" and category not in allowlisted_write_categories:
            errors.append(f"allowed_write_targets.{category} is not in gateway write-target allowlists")

    # Check autonomous_promotion is false
    promotion = manifest.get("promotion_behavior", {})
    if promotion.get("autonomous_promotion", True) is not False:
        errors.append("promotion_behavior.autonomous_promotion must be false")

    coordination = manifest.get("coordination_policy", {})
    required_coordination_fields = (
        "cross_runtime_coordination",
        "direct_runtime_state_in_chat",
        "actionable_ingress_translation",
        "coordination_source_of_truth",
    )
    for field in required_coordination_fields:
        if field not in coordination:
            errors.append(f"coordination_policy.{field} is required")

    allowed_coordination_modes = {"bus-required", "not-applicable"}
    mode = coordination.get("cross_runtime_coordination")
    if mode not in allowed_coordination_modes:
        errors.append(
            "coordination_policy.cross_runtime_coordination must be one of "
            f"{sorted(allowed_coordination_modes)}, got: {mode!r}"
        )

    if coordination.get("coordination_source_of_truth") != "runtime/agent_bus/":
        errors.append(
            "coordination_policy.coordination_source_of_truth must be 'runtime/agent_bus/'"
        )

    allowed_ingress_translation = {"required", "not-applicable"}
    translation = coordination.get("actionable_ingress_translation")
    if translation not in allowed_ingress_translation:
        errors.append(
            "coordination_policy.actionable_ingress_translation must be one of "
            f"{sorted(allowed_ingress_translation)}, got: {translation!r}"
        )

    if not isinstance(coordination.get("direct_runtime_state_in_chat"), bool):
        errors.append("coordination_policy.direct_runtime_state_in_chat must be boolean")

    return errors


def validate_all_manifests() -> dict[str, list[str]]:
    """Validate all adapter manifests. Returns {adapter_id: [errors]}."""
    results = {}
    for adapter_id, manifest in load_all_manifests().items():
        errors = validate_manifest(manifest)
        if errors:
            results[adapter_id] = errors
    return results


# ---------------------------------------------------------------------------
# Provenance minimum seam
# ---------------------------------------------------------------------------

PROVENANCE_MINIMUM_WRITE_ROOTS = (
    "02_KNOWLEDGE/",
)

PROVENANCE_MINIMUM_ANCHOR_FIELDS = (
    "promoted_from",
    "source_package_id",
    "source_ids",
    "source_refs",
    "provenance_ref",
    "capture_id",
)


def path_requires_provenance_minimums(write_target: str) -> bool:
    """Return True when a write target is a promoted knowledge note path."""
    normalized = str(write_target).replace("\\", "/")
    return normalized.endswith(".md") and any(
        normalized == root.rstrip("/") or normalized.startswith(root)
        for root in PROVENANCE_MINIMUM_WRITE_ROOTS
    )



def check_provenance_minimums(write_target: str, frontmatter: Optional[dict]) -> tuple[bool, str]:
    """Narrow Gate-adjacent seam for promoted-note provenance minimums.

    This does NOT implement full Context Governance Layer behavior.
    It only answers whether a note that would land under 02_KNOWLEDGE/
    carries the minimum provenance anchors needed for an honest promotion.
    Non-knowledge paths are treated as not applicable.
    """
    if not path_requires_provenance_minimums(write_target):
        return True, f"provenance minimums not applicable to path: {write_target}"

    if not isinstance(frontmatter, dict):
        return False, "provenance minimums failed: promoted knowledge notes require frontmatter"

    verification_status = str(frontmatter.get("verification_status") or "").strip()
    if not verification_status:
        return False, "provenance minimums failed: missing verification_status"

    for field in PROVENANCE_MINIMUM_ANCHOR_FIELDS:
        value = frontmatter.get(field)
        if isinstance(value, str) and value.strip():
            return True, f"provenance minimums passed via {field}"
        if isinstance(value, list) and any(isinstance(item, str) and item.strip() for item in value):
            return True, f"provenance minimums passed via {field}"

    required = ", ".join(PROVENANCE_MINIMUM_ANCHOR_FIELDS)
    return False, (
        "provenance minimums failed: promoted knowledge notes require at least one provenance anchor field "
        f"({required})"
    )


# ---------------------------------------------------------------------------
# Policy checks
# ---------------------------------------------------------------------------

RUNTIME_OPERATION_POLICIES: dict[str, dict[str, Any]] = {
    "agent_bus.ingress.discord": {
        "target_manifest_required": True,
        "coordination_sensitive": True,
        "via_bus_required": True,
        "allow_control_surface_actor": True,
        "control_plane_transport": "discord",
    },
    "agent_bus.task.create": {
        "actor_manifest_required": True,
        "target_manifest_required": True,
        "coordination_sensitive": True,
        "via_bus_required": True,
        "control_plane_transport": "runtime/agent_bus/",
    },
    "agent_bus.task.claim": {
        "actor_manifest_required": True,
        "control_plane_transport": "runtime/agent_bus/",
    },
    "agent_bus.task.update": {
        "actor_manifest_required": True,
        "control_plane_transport": "runtime/agent_bus/",
    },
    "agent_bus.task.cleanup": {
        "actor_manifest_required": True,
        "control_plane_transport": "runtime/agent_bus/",
    },
    "agent_bus.task.reclaim": {
        "actor_manifest_required": True,
        "control_plane_transport": "runtime/agent_bus/",
    },
    "agent_bus.heartbeat": {
        "actor_manifest_required": True,
        "control_plane_transport": "runtime/agent_bus/",
    },
    "agent_bus.watch": {
        "actor_manifest_required": True,
        "control_plane_transport": "runtime/agent_bus/",
    },
    "agent_bus.expire_stale": {
        "allow_cli_operator": True,
        "control_plane_transport": "runtime/agent_bus/",
    },
    "config.set": {
        "allow_cli_operator": True,
        "write_target_categories": ["config_state"],
    },
    "schedule.enable": {
        "allow_cli_operator": True,
        "write_target_categories": ["schedule_state"],
    },
    "schedule.disable": {
        "allow_cli_operator": True,
        "write_target_categories": ["schedule_state"],
    },
    "events.emit": {
        "allow_cli_operator": True,
        "write_target_categories": ["event_state"],
    },
    "events.dispatch": {
        "allow_cli_operator": True,
        "write_target_categories": ["event_state"],
    },
    "gateway.workflow.dispatch": {
        "actor_manifest_required": True,
    },
    "gateway.workflow.invoke_bounded": {
        "actor_manifest_required": True,
    },
    "sbp.delivery.discord.webhook_send": {
        "allow_cli_operator": True,
        "external_api": "delivery.discord_webhook",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "sbp.delivery.whop.post": {
        "allow_cli_operator": True,
        "external_api": "delivery.whop_api",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "browser.open": {
        "allow_cli_operator": True,
        "write_target_categories": ["browser_operator_outputs"],
        "external_api": "browser.navigation",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "browser.inspect": {
        "allow_cli_operator": True,
        "write_target_categories": ["browser_operator_outputs"],
        "external_api": "browser.navigation",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "browser.snapshot": {
        "allow_cli_operator": True,
        "write_target_categories": ["browser_operator_outputs"],
        "external_api": "browser.navigation",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "browser.screenshot": {
        "allow_cli_operator": True,
        "write_target_categories": ["browser_operator_outputs"],
        "external_api": "browser.navigation",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "agent.register": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_registry_state"],
    },
    "agent.lifecycle.transition": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_registry_state"],
    },
    "graph_store.snapshot.write": {
        "allow_cli_operator": True,
        "write_target_categories": ["graph_store_snapshots"],
    },
    "graph_store.identity.write": {
        "allow_cli_operator": True,
        "write_target_categories": ["graph_store_identity"],
    },
    "graph_store.migration.write": {
        "allow_cli_operator": True,
        "write_target_categories": ["graph_store_migrations"],
    },
    "lifecycle.coordination_watch.run": {
        "allow_cli_operator": True,
        "control_plane_transport": "runtime/agent_bus/",
    },
    "lifecycle.coordination_watch_supervisor.start": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
        "external_api": "host.process",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "lifecycle.coordination_watch_supervisor.stop": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
        "external_api": "host.process",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "lifecycle.coordination_watch_supervisor.cleanup_stale": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
    },
    "lifecycle.coordination_watch_bootstrap.install": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
    },
    "lifecycle.coordination_watch_bootstrap.apply": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
        "external_api": "host.scheduler",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "lifecycle.coordination_watch_bootstrap.verify": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.coordination_watch_bootstrap.activation_report": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.coordination_watch_bootstrap.activation_checklist": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surfaces.report": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surface_settings.report": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surface_toggle.plan": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surface_mutation.contract": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surface_approval.request": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_activity"],
    },
    "lifecycle.startup_surface_approval.decision": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_activity"],
    },
    "lifecycle.startup_surface_approval.consumption": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_activity", "runtime_lifecycle_state"],
    },
    "lifecycle.startup_surface_executor.preflight": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surface_transaction.order_report": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surface_executor.readiness": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surface_host_boundary.policy": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surface_host_mutation.audit_template": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surface_success_marker.evidence_verifier": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surface_success_marker.acceptance_policy": {
        "allow_cli_operator": True,
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.startup_surface_host_mutation.executor": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_activity", "runtime_lifecycle_state", "host_startup_registration"],
        "external_api": "host.startup_folder",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "lifecycle.startup_surface.gateway.enable": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state", "host_startup_registration"],
        "external_api": "host.startup_folder",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "lifecycle.startup_surface.gateway.disable": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state", "host_startup_registration"],
        "external_api": "host.startup_folder",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "lifecycle.startup_surface.coordination_watch_supervisor.enable": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
        "external_api": "host.process",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "lifecycle.startup_surface.coordination_watch_supervisor.disable": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
        "external_api": "host.process",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "lifecycle.startup_surface.coordination_watch_bootstrap.enable": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
        "external_api": "host.scheduler",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "lifecycle.startup_surface.coordination_watch_bootstrap.disable": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
        "external_api": "host.scheduler",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "lifecycle.coordination_watch_bootstrap.unregister": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
        "external_api": "host.scheduler",
        "external_side_effect": True,
        "allow_cli_operator_external_api": True,
        "allow_cli_operator_external_side_effect": True,
    },
    "lifecycle.coordination_watch_bootstrap.handoff": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
    },
    "lifecycle.coordination_watch_bootstrap.reboot_verify": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
    },
    "lifecycle.coordination_watch_bootstrap.capture_success": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.coordination_watch_bootstrap.reconcile_reboot_result": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
        "external_api": "host.scheduler",
        "allow_cli_operator_external_api": True,
    },
    "lifecycle.coordination_watch_bootstrap.remove": {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_lifecycle_state"],
    },
    "lifecycle.hermes_gateway_config.backup": {
        "allow_cli_operator": True,
        "write_target_categories": ["private_runtime_config"],
    },
    "lifecycle.hermes_gateway_config.apply": {
        "allow_cli_operator": True,
        "write_target_categories": ["private_runtime_config"],
    },
    "setup.init.write": {
        "allow_cli_operator": True,
    },
    "setup.provider.apply": {
        "allow_cli_operator": True,
        "write_target_categories": ["setup_state"],
    },
    "setup.integration.apply": {
        "allow_cli_operator": True,
        "write_target_categories": ["setup_state"],
    },
    "setup.state.set": {
        "allow_cli_operator": True,
        "write_target_categories": ["setup_state"],
    },
    "scaffold.project.generate": {
        "allow_cli_operator": True,
        "write_target_categories": ["draft_outputs"],
    },
    "scaffold.workspace.generate": {
        "allow_cli_operator": True,
        "write_target_categories": ["draft_outputs"],
    },
    "scaffold.brain.generate": {
        "allow_cli_operator": True,
        "write_target_categories": ["draft_outputs"],
    },
    "osril.approval_response": {
        "allow_cli_operator": True,
        "write_target_categories": ["osril_approval_state", "osril_run_state"],
    },
    "osril.approval_resume": {
        "allow_cli_operator": True,
        "write_target_categories": ["osril_approval_state", "osril_run_state"],
    },
    RUNTIME_PROVIDER_LIVE_PROBE_OPERATION: {
        "allow_cli_operator": True,
        "write_target_categories": ["runtime_provider_state"],
        "external_api_required": True,
        "allow_cli_operator_external_api": True,
        "approval_required": True,
        "approval_schema": RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID,
    },
    RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION: {
        "allow_cli_operator": True,
        "approval_required": True,
        "approval_schema": RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
    },
    BROWSER_CDP_READ_ONLY_PROOF_OPERATION: {
        "allow_cli_operator": True,
        "write_target_categories": ["browser_operator_outputs", "inputs_folder"],
        "external_api": "browser.navigation",
        "allow_cli_operator_external_api": True,
        "approval_required": True,
        "approval_schema": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
    },
    "siteops.browser_skill_candidate.apply_trusted_artifacts": {
        "allow_cli_operator": True,
        "gateway_write_categories": [
            "browser_skills_inactive_review",
            "siteops_skill_cards_inactive_review",
        ],
        "write_target_categories": [
            "browser_skills_inactive_review",
            "siteops_skill_cards_inactive_review",
        ],
    },
    "siteops.browser_skill_candidate.activate_trusted_artifact": {
        "allow_cli_operator": True,
        "gateway_write_categories": [
            "browser_skills_inactive_review",
            "siteops_skill_cards_inactive_review",
            "siteops_activation_records",
        ],
        "write_target_categories": [
            "browser_skills_inactive_review",
            "siteops_skill_cards_inactive_review",
            "siteops_activation_records",
        ],
    },
}


def get_runtime_operation_approval_schema(
    operation: str,
    *,
    provider_id: str | None = None,
    model: str | None = None,
    runtime: str | None = None,
    external_api: str | None = None,
    source_command: str | None = None,
) -> dict[str, Any] | None:
    """Return the non-mutating approval schema for a Gate-governed operation.

    This surfaces the approval artifact shape only. It does not record an
    approval decision, read credentials, execute network calls, or mutate
    runtime/provider state.
    """
    policy = RUNTIME_OPERATION_POLICIES.get(operation)
    if not policy or not policy.get("approval_schema"):
        return None

    schema_id = str(policy["approval_schema"])
    if operation == BROWSER_CDP_READ_ONLY_PROOF_OPERATION:
        approval_request_template = {
            "record_type": "browser_cdp_read_only_proof_approval_request",
            "schema_version": 1,
            "approval_schema_id": schema_id,
            "operation": operation,
            "operator_request_id": "<operator-request-id>",
            "gate_approval_id": "<gate-approval-id>",
            "runtime": runtime or "<runtime>",
            "target_url": "<local-or-allowlisted-url>",
            "allowed_domains": ["127.0.0.1", "localhost"],
            "cdp_endpoint": "http://127.0.0.1:<port>",
            "launch_strategy": "chaseos_launch_isolated",
            "browser_profile_policy": "throwaway_only",
            "allowed_actions": [
                "page.navigate",
                "page.capture_screenshot",
                "dom.snapshot",
                "page.read_title",
                "page.read_url",
                "page.read_visible_text",
                "wait_for",
            ],
            "artifact_targets": [
                "07_LOGS/Browser-Runs/**",
                "07_LOGS/Agent-Activity/**",
                "03_INPUTS/Browser-Skill-Candidates/**",
            ],
            "screenshot_retention": "log_artifact_only_redacted_if_needed",
            "secret_policy": {
                "credentials_allowed": False,
                "cookies_allowed": False,
                "session_tokens_allowed": False,
                "real_profile_allowed": False,
                "raw_cdp_allowed": False,
                "runtime_evaluate_allowed": False,
            },
            "approval_effect": (
                "Authorizes review of one future local read-only CDP browser proof "
                "only after a future executor validates this approval artifact. "
                "This request packet does not connect to CDP or launch a browser."
            ),
        }
        return {
            "schema_version": 1,
            "approval_schema_id": schema_id,
            "operation": operation,
            "approval_required": True,
            "approval_status": "missing",
            "required_fields": list(BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_REQUIRED_FIELDS),
            "required_policy_checks": [
                "operation must be browser.cdp.read_only_proof",
                "target_url domain must be local or explicitly allowlisted",
                "cdp_endpoint must be local-only and not a public tunnel",
                "launch_strategy must create an isolated ChaseOS browser context",
                "browser_profile_policy must be throwaway_only",
                "allowed_actions must exclude raw CDP, Runtime.evaluate, cookie/session reads, downloads, uploads, and DOM mutation",
                "artifact targets must remain limited to browser run logs, agent activity, and untrusted skill candidates",
                "approval does not authorize trusted skill writes, activation, provider calls, Agent Bus enqueue, or canonical writeback",
            ],
            "approval_request_template": approval_request_template,
            "approval_request_written": False,
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "real_profile_used": False,
            "credential_value_read": False,
            "cookie_or_session_read": False,
            "trusted_skill_written": False,
            "canonical_files_mutated": False,
            "denied_without_approval": [
                "cdp_socket_connection",
                "browser_launch",
                "real_profile_attachment",
                "credential_or_cookie_access",
                "raw_cdp_passthrough",
                "trusted_skill_write",
                "skill_activation",
                "canonical_file_write",
            ],
            "source_command": source_command,
        }

    if operation == RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION:
        approval_request_template = {
            "record_type": "runtime_provider_config_apply_approval_request",
            "schema_version": 1,
            "approval_schema_id": schema_id,
            "operation": operation,
            "operator_request_id": "<operator-request-id>",
            "gate_approval_id": "<gate-approval-id>",
            "proposal_id": "<rpgl-provider-config-proposal-id>",
            "queue_item_id": "<rpglq-id>",
            "expected_primary_model": model or "gpt-5.5",
            "proposed_changes_digest_sha256": "<sha256-of-proposed-changes>",
            "target_paths": [
                "runtime/hermes/model_config.yaml",
                "runtime/openclaw/model_config.yaml",
                "runtime/setup_state.json",
            ],
            "rollback_plan": {
                "required": True,
                "method": "capture exact previous values before write and restore on failed verification",
            },
            "post_apply_verification": [
                "rerun chaseos runtime provider config-report",
                "rerun chaseos runtime provider config-apply-preflight <proposal_id>",
                "verify provider_state was not mutated by config apply",
                "verify local fallback num_ctx remains at or below 16384 if an active local config target exists",
            ],
            "files_modified_expected": True,
            "approval_effect": (
                "Authorizes one future provider config apply attempt only after "
                "a future executor validates this approval artifact. This request "
                "packet does not edit provider config."
            ),
        }
        return {
            "schema_version": 1,
            "approval_schema_id": schema_id,
            "operation": operation,
            "approval_required": True,
            "approval_status": "missing",
            "required_fields": list(RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_REQUIRED_FIELDS),
            "required_policy_checks": [
                "operation must be runtime.provider.config_apply",
                "proposal_id and queue_item_id must match a valid RPGL provider config proposal",
                "proposal digest and current-value preflight must still pass",
                "target_paths must be limited to reviewed provider config/setup files",
                "rollback_plan must capture previous values before any write",
                "post_apply_verification must rerun config-report and apply-preflight",
                "approval does not authorize provider calls, secret reads, gateway restart, queue drain, or broad canonical writes",
            ],
            "approval_request_template": approval_request_template,
            "approval_request_written": False,
            "apply_executor_implemented": False,
            "provider_config_mutated": False,
            "setup_state_mutated": False,
            "provider_state_mutated": False,
            "secret_value_read": False,
            "live_network_call_attempted": False,
            "queue_drained": False,
            "canonical_files_mutated": False,
            "denied_without_approval": [
                "provider_config_edit",
                "setup_state_edit",
                "provider_state_update",
                "secret_value_read",
                "external_provider_call",
                "queue_retry_or_drain",
                "gateway_restart",
                "canonical_file_write",
            ],
            "source_command": source_command,
        }

    if operation != RUNTIME_PROVIDER_LIVE_PROBE_OPERATION:
        return {
            "schema_version": 1,
            "approval_schema_id": schema_id,
            "operation": operation,
            "approval_required": bool(policy.get("approval_required")),
            "approval_request_written": False,
            "live_action_executed": False,
            "source_command": source_command,
        }

    timeout_policy = {
        "first_token_timeout_sec": 30,
        "no_chunk_timeout_sec": 60,
        "total_wall_time_sec": 180,
        "max_fallback_attempts": 1,
    }
    approval_request_template = {
        "record_type": "runtime_provider_live_probe_approval_request",
        "schema_version": 1,
        "approval_schema_id": schema_id,
        "operation": operation,
        "operator_request_id": "<operator-request-id>",
        "gate_approval_id": "<gate-approval-id>",
        "provider_id": provider_id or "<provider-id>",
        "model": model or "<model>",
        "runtime": runtime or "<runtime>",
        "probe_scope": "provider_health_check_only",
        "external_api_id": external_api or "<provider.external_api_id>",
        "timeout_policy": timeout_policy,
        "secret_reference_metadata_only": True,
        "credential_values_allowed": False,
        "payload_values_logged": False,
        "approval_effect": (
            "Authorizes one future live provider health probe only after a "
            "future executor validates this approval artifact. This request "
            "packet does not execute the probe."
        ),
    }
    return {
        "schema_version": 1,
        "approval_schema_id": schema_id,
        "operation": operation,
        "approval_required": True,
        "approval_status": "missing",
        "required_fields": list(RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_REQUIRED_FIELDS),
        "required_policy_checks": [
            "operation must be runtime.provider.live_probe",
            "external_api_id must be Gate allowlisted",
            "provider_id, model, runtime, and probe_scope must match the RPGL preflight payload",
            "secret references are metadata-only; credential values must not be logged",
            "future executor must enforce first-token, no-chunk, wall-time, and attempt limits",
            "future executor may update provider state/audit only inside runtime_provider_state targets",
            "approval does not authorize queue drain, gateway restart, config edits, or canonical writes",
        ],
        "approval_request_template": approval_request_template,
        "approval_request_written": False,
        "live_network_call_attempted": False,
        "secret_value_read": False,
        "provider_state_mutated": False,
        "queue_mutated": False,
        "canonical_files_mutated": False,
        "denied_without_approval": [
            "external_provider_call",
            "secret_value_read",
            "provider_state_update",
            "queue_retry_or_drain",
            "gateway_restart",
            "provider_config_edit",
            "canonical_file_write",
        ],
        "source_command": source_command,
    }


def _normalize_adapter_id(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized.lower().replace("_", "-")


def _load_manifest_for_policy(adapter_id: str | None) -> tuple[str | None, dict]:
    normalized = _normalize_adapter_id(adapter_id)
    if not normalized:
        return None, {}

    direct = load_adapter_manifest(normalized)
    if direct:
        return str(direct.get("adapter_id") or normalized), direct

    for manifest in load_all_manifests().values():
        declared = str(manifest.get("adapter_id") or "").strip().lower()
        name = str(manifest.get("adapter_name") or "").strip().lower()
        if normalized in {declared, name}:
            return str(manifest.get("adapter_id") or normalized), manifest

    return normalized, {}


def _manifest_is_active(adapter_id: str, manifest: dict) -> tuple[bool, str]:
    status = str(manifest.get("status") or "").strip().lower()
    if status == "active":
        return True, "active"
    return False, f"Adapter '{adapter_id}' is not active (status: {status or 'unknown'})."


def check_runtime_operation(
    operation: str,
    *,
    actor_adapter_id: str | None = None,
    target_runtime: str | None = None,
    task_type: str | None = None,
    write_targets: list[str] | None = None,
    coordination_sensitive: bool | None = None,
    via_bus: bool | None = None,
    external_api: str | None = None,
    external_side_effect: bool = False,
    control_plane_transport: str | None = None,
) -> tuple[bool, str]:
    """Deny-by-default runtime operation policy check.

    Unknown operations are blocked. Known operations must satisfy their explicit
    policy and the adapter manifests they rely on.
    """
    policy = RUNTIME_OPERATION_POLICIES.get(operation)
    if policy is None:
        return False, f"Runtime operation '{operation}' is not allowlisted."

    if policy.get("approval_required"):
        schema = str(policy.get("approval_schema") or "unknown")
        return False, f"Runtime operation '{operation}' requires explicit Gate approval schema '{schema}'."

    actor_id: str | None = None
    actor_manifest: dict = {}
    if policy.get("actor_manifest_required") or actor_adapter_id:
        actor_id, actor_manifest = _load_manifest_for_policy(actor_adapter_id)
        if not actor_id or not actor_manifest:
            return False, f"Runtime operation '{operation}' requires a valid actor adapter manifest."
        active, reason = _manifest_is_active(actor_id, actor_manifest)
        if not active:
            return False, reason

    target_id: str | None = None
    target_manifest: dict = {}
    if policy.get("target_manifest_required") or target_runtime:
        target_id, target_manifest = _load_manifest_for_policy(target_runtime)
        if not target_id or not target_manifest:
            return False, f"Runtime operation '{operation}' requires a valid target runtime manifest."
        active, reason = _manifest_is_active(target_id, target_manifest)
        if not active:
            return False, reason

    if not actor_manifest and not target_manifest and not policy.get("allow_cli_operator"):
        return False, f"Runtime operation '{operation}' has no approved actor or target manifest."

    gateway_write_categories = [str(item) for item in policy.get("gateway_write_categories") or []]
    if gateway_write_categories:
        for write_target in write_targets or []:
            if not any(check_gateway_write_target(category, write_target)[0] for category in gateway_write_categories):
                categories = ", ".join(gateway_write_categories)
                return False, (
                    f"Write target '{write_target}' is outside allowlisted gateway categories for "
                    f"runtime operation '{operation}' ({categories})."
                )

    effective_transport = control_plane_transport or policy.get("control_plane_transport")
    if effective_transport:
        allowed, reason = check_control_plane_transport(str(effective_transport))
        if not allowed:
            return False, reason

    policy_external_api = policy.get("external_api")
    if policy_external_api:
        policy_external_api = str(policy_external_api)
        if external_api and external_api != policy_external_api:
            return False, (
                f"Runtime operation '{operation}' requires external API "
                f"'{policy_external_api}', not '{external_api}'."
            )
    effective_external_api = str(policy_external_api or external_api or "").strip() or None
    effective_external_side_effect = external_side_effect or bool(policy.get("external_side_effect"))

    if policy.get("external_api_required") and not effective_external_api:
        return False, f"Runtime operation '{operation}' requires an explicit external API allowlist id."

    if effective_external_side_effect and not effective_external_api:
        return False, f"Runtime operation '{operation}' requires an explicit external API allowlist id."

    if effective_external_api:
        allowed, reason = check_external_api(effective_external_api)
        if not allowed:
            return False, reason
        manifest = actor_manifest or target_manifest
        cli_operator_external_allowed = bool(
            policy.get("allow_cli_operator")
            and policy.get("allow_cli_operator_external_api")
            and not manifest
        )
        if not cli_operator_external_allowed:
            adapter_id = actor_id or target_id or "unknown"
            side_effect_policy = manifest.get("external_side_effect_policy") or {}
            api_policy = side_effect_policy.get("may_call_external_apis")
            if api_policy not in {"yes", "with-approval"}:
                return False, f"Adapter '{adapter_id}' is not approved for external API calls."

    if effective_external_side_effect:
        manifest = actor_manifest or target_manifest
        cli_operator_side_effect_allowed = bool(
            policy.get("allow_cli_operator")
            and policy.get("allow_cli_operator_external_side_effect")
            and not manifest
        )
        if not cli_operator_side_effect_allowed:
            adapter_id = actor_id or target_id or "unknown"
            side_effect_policy = manifest.get("external_side_effect_policy") or {}
            write_policy = side_effect_policy.get("may_write_to_external_systems")
            if write_policy not in {"yes", "with-approval"}:
                return False, f"Adapter '{adapter_id}' is not approved for external side effects."

    if task_type and actor_id:
        allowed, reason = check_task_type(actor_id, task_type)
        if not allowed:
            return False, reason

    for write_target in write_targets or []:
        if actor_id:
            allowed, reason = check_write_permission(actor_id, write_target)
            if not allowed:
                return False, reason
            continue

        policy_categories = policy.get("write_target_categories") or gateway_write_categories or []
        if not policy_categories:
            return False, f"Runtime operation '{operation}' cannot check write target without an actor adapter."

        if not any(
            check_gateway_write_target(str(category), write_target)[0]
            for category in policy_categories
        ):
            categories = ", ".join(str(category) for category in policy_categories)
            return (
                False,
                f"Write target '{write_target}' is outside explicit allowlists for operation "
                f"'{operation}' ({categories}).",
            )

    effective_coordination_sensitive = (
        policy.get("coordination_sensitive")
        if coordination_sensitive is None
        else coordination_sensitive
    )
    effective_via_bus = policy.get("via_bus_required") if via_bus is None else via_bus
    if effective_coordination_sensitive:
        coordination_adapter = actor_id or target_id
        if not coordination_adapter:
            return False, f"Runtime operation '{operation}' requires a coordination adapter."
        allowed, reason = check_coordination_path(
            coordination_adapter,
            coordination_sensitive=True,
            via_bus=bool(effective_via_bus),
            target_runtime=target_runtime,
        )
        if not allowed:
            return False, reason

        if target_id and target_id != coordination_adapter:
            allowed, reason = check_coordination_path(
                target_id,
                coordination_sensitive=True,
                via_bus=bool(effective_via_bus),
                target_runtime=actor_adapter_id,
            )
            if not allowed:
                return False, reason

    return True, f"Runtime operation '{operation}' allowed."


def check_write_permission(adapter_id: str, write_target: str) -> tuple[bool, str]:
    """Check if the adapter is allowed to write to the given target.

    Args:
        adapter_id: The adapter ID
        write_target: Path of the file being written (relative to vault root)

    Returns:
        (allowed: bool, reason: str)
    """
    manifest = load_adapter_manifest(adapter_id)
    if not manifest:
        return False, f"No manifest found for adapter: {adapter_id}"

    # Check if protected file
    protected_files = load_protected_files()
    target_path = Path(write_target)
    for pf in protected_files:
        if str(target_path).endswith(pf) or target_path == Path(pf):
            behavior = manifest.get("protected_file_behavior", "block")
            if behavior == "block":
                return False, f"Protected file — explicit user approval required: {write_target}"
            elif behavior == "require-approval":
                return False, f"Protected file — explicit per-file approval required: {write_target}"
            # advisory-only: no vault access possible anyway
            return False, f"Protected file — advisory surface cannot write: {write_target}"

    # Check explicitly denied targets from the adapter manifest
    normalized_target = write_target.replace("\\", "/")
    for denied_pattern in manifest.get("explicitly_denied_write_targets", []):
        normalized_pattern = str(denied_pattern).replace("\\", "/")
        if fnmatch.fnmatch(normalized_target, normalized_pattern):
            return False, f"Write target is explicitly denied by adapter manifest: {write_target}"

    write_targets = manifest.get("allowed_write_targets", {})
    if not write_targets.get("protected_files", False):
        for pf in protected_files:
            if pf in write_target:
                return False, f"Write target is a protected file: {write_target}"

    enabled_categories = [
        category
        for category, enabled in write_targets.items()
        if enabled is True and category != "protected_files"
    ]
    for category in enabled_categories:
        allowed, reason = check_gateway_write_target(category, write_target)
        if allowed:
            return True, reason

    if enabled_categories:
        categories = ", ".join(sorted(enabled_categories))
        return (
            False,
            f"Write target '{write_target}' is outside explicit allowlists for adapter "
            f"'{adapter_id}' ({categories}).",
        )

    return False, f"Adapter '{adapter_id}' has no enabled write-target allowlist categories."


def check_task_type(adapter_id: str, task_type: str) -> tuple[bool, str]:
    """Check if the adapter is allowed to run the given task type.

    Args:
        adapter_id: The adapter ID
        task_type: The task type slug

    Returns:
        (allowed: bool, reason: str)
    """
    manifest = load_adapter_manifest(adapter_id)
    if not manifest:
        return False, f"No manifest found for adapter: {adapter_id}"

    allowed_types = manifest.get("allowed_task_types", [])
    global_allowed_types = set((load_gateway_allowlists().get("task_types") or []))
    if task_type not in global_allowed_types:
        return False, f"Task type '{task_type}' is not in the global gateway task allowlist"

    if task_type in allowed_types:
        return True, "allowed"

    return False, f"Task type '{task_type}' is not in allowed_task_types for adapter '{adapter_id}'"


def check_coordination_path(
    adapter_id: str,
    coordination_sensitive: bool,
    via_bus: bool,
    target_runtime: str | None = None,
) -> tuple[bool, str]:
    """Check whether coordination-sensitive work is using the required ChaseOS bus path.

    This helper is for OS-level enforcement of the constitutional rule:
    operator/control surfaces are ingress, and cross-runtime coordination-sensitive
    work must become ChaseOS-owned structured state before machine-to-machine
    handling continues.
    """
    manifest = load_adapter_manifest(adapter_id)
    if not manifest:
        return False, f"No manifest found for adapter: {adapter_id}"

    if not coordination_sensitive:
        return True, "coordination path not required"

    coordination = manifest.get("coordination_policy", {})
    mode = coordination.get("cross_runtime_coordination")
    target_note = f" targeting runtime '{target_runtime}'" if target_runtime else ""

    if mode == "not-applicable":
        return (
            False,
            f"Adapter '{adapter_id}' is not approved for coordination-sensitive runtime work{target_note}.",
        )

    if mode != "bus-required":
        return (
            False,
            f"Adapter '{adapter_id}' lacks a valid coordination policy for runtime coordination.",
        )

    if not via_bus:
        return (
            False,
            "Coordination-sensitive runtime work"
            f"{target_note} must be translated into runtime/agent_bus/ before coordination continues.",
        )

    return True, "allowed via runtime/agent_bus/"


# ---------------------------------------------------------------------------
# CLI interface (when run directly)
# ---------------------------------------------------------------------------


def main():
    """Simple CLI for Gate validation and policy checks."""
    if len(sys.argv) < 2:
        print("ChaseOS Gate — Usage:")
        print("  python chaseos_gate.py validate            # Validate all adapter manifests")
        print("  python chaseos_gate.py list                # List all registered adapters")
        print("  python chaseos_gate.py allowlists          # Show gateway allowlist summary")
        print("  python chaseos_gate.py show <adapter-id>  # Show adapter manifest")
        print("  python chaseos_gate.py check-write <adapter-id> <file-path>")
        print("  python chaseos_gate.py check-task <adapter-id> <task-type>")
        print("  python chaseos_gate.py check-external-api <api-id>")
        print("  python chaseos_gate.py check-transport <transport>")
        print("  python chaseos_gate.py check-credential-reference <kind> <target>")
        print(
            "  python chaseos_gate.py check-coordination <adapter-id> <coordination-sensitive:true|false> <via-bus:true|false> [target-runtime]"
        )
        if yaml is None:
            print("\nNote: PyYAML not installed, using simple YAML fallback parser.")
        sys.exit(0)

    command = sys.argv[1]

    if command == "validate":
        errors = validate_all_manifests()
        if not errors:
            print("All adapter manifests are valid.")
        else:
            for adapter_id, errs in errors.items():
                print(f"\n{adapter_id}:")
                for e in errs:
                    print(f"  - {e}")
            sys.exit(1)

    elif command == "list":
        manifests = load_all_manifests()
        if not manifests:
            print("No adapter manifests found in runtime/policy/adapters/")
        for adapter_id, manifest in manifests.items():
            status = manifest.get("status", "unknown")
            name = manifest.get("adapter_name", adapter_id)
            print(f"  {adapter_id:20s} [{status:8s}]  {name}")

    elif command == "allowlists":
        allowlists = load_gateway_allowlists()
        if not allowlists:
            print("Gateway allowlists are missing or invalid.")
            sys.exit(1)
        print(json.dumps(allowlists, indent=2))

    elif command == "show" and len(sys.argv) >= 3:
        adapter_id = sys.argv[2]
        manifest = load_adapter_manifest(adapter_id)
        if not manifest:
            print(f"No manifest found for: {adapter_id}")
            sys.exit(1)
        if yaml:
            print(yaml.dump(manifest, default_flow_style=False))
        else:
            print(json.dumps(manifest, indent=2))

    elif command == "check-write" and len(sys.argv) >= 4:
        adapter_id = sys.argv[2]
        write_target = sys.argv[3]
        allowed, reason = check_write_permission(adapter_id, write_target)
        print(f"Write permission: {'ALLOWED' if allowed else 'BLOCKED'}")
        print(f"Reason: {reason}")
        sys.exit(0 if allowed else 1)

    elif command == "check-task" and len(sys.argv) >= 4:
        adapter_id = sys.argv[2]
        task_type = sys.argv[3]
        allowed, reason = check_task_type(adapter_id, task_type)
        print(f"Task allowed: {'YES' if allowed else 'NO'}")
        print(f"Reason: {reason}")
        sys.exit(0 if allowed else 1)

    elif command == "check-external-api" and len(sys.argv) >= 3:
        allowed, reason = check_external_api(sys.argv[2])
        print(f"External API: {'ALLOWED' if allowed else 'BLOCKED'}")
        print(f"Reason: {reason}")
        sys.exit(0 if allowed else 1)

    elif command == "check-transport" and len(sys.argv) >= 3:
        allowed, reason = check_control_plane_transport(sys.argv[2])
        print(f"Control-plane transport: {'ALLOWED' if allowed else 'BLOCKED'}")
        print(f"Reason: {reason}")
        sys.exit(0 if allowed else 1)

    elif command == "check-credential-reference" and len(sys.argv) >= 4:
        allowed, reason = check_credential_reference(sys.argv[2], sys.argv[3])
        print(f"Credential reference: {'ALLOWED' if allowed else 'BLOCKED'}")
        print(f"Reason: {reason}")
        sys.exit(0 if allowed else 1)

    elif command == "check-coordination" and len(sys.argv) >= 5:
        adapter_id = sys.argv[2]
        coordination_sensitive = sys.argv[3].lower() == "true"
        via_bus = sys.argv[4].lower() == "true"
        target_runtime = sys.argv[5] if len(sys.argv) >= 6 else None
        allowed, reason = check_coordination_path(
            adapter_id,
            coordination_sensitive=coordination_sensitive,
            via_bus=via_bus,
            target_runtime=target_runtime,
        )
        print(f"Coordination path: {'ALLOWED' if allowed else 'BLOCKED'}")
        print(f"Reason: {reason}")
        sys.exit(0 if allowed else 1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
