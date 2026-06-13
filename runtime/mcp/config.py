"""Configuration loading for the internal ChaseOS Runtime MCP server."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.mcp.errors import ERR_CONFIG_INVALID, system_error
from runtime.mcp.types import MCPConfig, RuntimeTrustConfig
from runtime.mcp.yaml_compat import safe_load


CONFIG_PATH = Path(__file__).with_name("config.yaml")
VALID_MODES = {"read_only", "read_plus_proposal", "draft_execution"}


class ConfigError(RuntimeError):
    """Raised when MCP config is missing or invalid."""


def detect_vault_root() -> Path:
    here = Path(__file__).resolve()
    vault_root = here.parents[2]
    if not (vault_root / "CLAUDE.md").exists():
        raise ConfigError("Could not detect vault root from runtime/mcp/config.py")
    return vault_root


def _as_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{field_name} must be a list of strings")
    return list(value)


def _require_mapping(data: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ConfigError(f"{field_name} must be a mapping")
    return data


def _relative_path(vault_root: Path, value: Any, field_name: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field_name} must be a non-empty relative path")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ConfigError(f"{field_name} must stay inside the vault")
    return vault_root / candidate


def load_config(vault_root: Path | None = None, config_path: Path | None = None) -> MCPConfig:
    """Load and validate Runtime MCP config. Invalid config fails closed."""
    root = Path(vault_root).resolve() if vault_root is not None else detect_vault_root()
    path = config_path or CONFIG_PATH
    try:
        raw = safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f"Could not load MCP config: {exc}") from exc

    data = _require_mapping(raw, "config")
    server = _require_mapping(data.get("server"), "server")
    safety = _require_mapping(data.get("safety"), "safety")
    paths = _require_mapping(data.get("paths"), "paths")
    runtimes_raw = _require_mapping(data.get("runtimes"), "runtimes")

    default_mode = safety.get("default_mode")
    if default_mode not in VALID_MODES:
        raise ConfigError("safety.default_mode contains an unknown mode")
    allowed_modes = _as_string_list(safety.get("allowed_modes"), "safety.allowed_modes")
    if not set(allowed_modes).issubset(VALID_MODES):
        raise ConfigError("safety.allowed_modes contains an unknown mode")

    fail_closed = _as_string_list(
        safety.get("fail_closed_surfaces"),
        "safety.fail_closed_surfaces",
    )
    fail_open = _as_string_list(
        safety.get("fail_open_surface_classes"),
        "safety.fail_open_surface_classes",
    )
    fail_open_surfaces = _as_string_list(
        safety.get("fail_open_surfaces"),
        "safety.fail_open_surfaces",
    )
    if not set(fail_open).issubset({"resource", "tool", "prompt"}):
        raise ConfigError("fail_open_surface_classes contains an unknown surface class")

    runtimes: dict[str, RuntimeTrustConfig] = {}
    for runtime_id, raw_runtime in runtimes_raw.items():
        if not isinstance(runtime_id, str):
            raise ConfigError("runtime ids must be strings")
        runtime_data = _require_mapping(raw_runtime, f"runtimes.{runtime_id}")
        trust_tier = runtime_data.get("trust_tier")
        if not isinstance(trust_tier, str) or not trust_tier:
            raise ConfigError(f"runtimes.{runtime_id}.trust_tier must be a non-empty string")
        runtime_modes = _as_string_list(
            runtime_data.get("allowed_modes"),
            f"runtimes.{runtime_id}.allowed_modes",
        )
        if not set(runtime_modes).issubset(VALID_MODES):
            raise ConfigError(f"runtimes.{runtime_id}.allowed_modes contains an unknown mode")
        runtimes[runtime_id] = RuntimeTrustConfig(
            runtime_id=runtime_id,
            trust_tier=trust_tier,
            allowed_modes=runtime_modes,
        )

    if "_unregistered" not in runtimes:
        raise ConfigError("runtimes._unregistered is required")

    return MCPConfig(
        vault_root=root,
        server_identity=str(server.get("identity") or "chaseos-runtime-mcp"),
        version=str(server.get("version") or "0.1.0"),
        transport=str(server.get("transport") or "stdio"),
        default_mode=default_mode,
        allowed_modes=allowed_modes,
        fail_closed_surfaces=fail_closed,
        fail_open_surface_classes=fail_open,
        fail_open_surfaces=fail_open_surfaces,
        staging_dir=_relative_path(root, paths.get("staging_dir"), "paths.staging_dir"),
        audit_dir=_relative_path(root, paths.get("audit_dir"), "paths.audit_dir"),
        operator_briefs_dir=_relative_path(
            root,
            paths.get("operator_briefs_dir"),
            "paths.operator_briefs_dir",
        ),
        runtimes=runtimes,
    )


def config_error_response(request_id: str, exc: Exception) -> dict[str, object]:
    error = system_error(ERR_CONFIG_INVALID, str(exc))
    return {"request_id": request_id, "ok": False, "error": error.to_dict()}
