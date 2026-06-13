"""Machine-readable VentureOps use-case registry loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback is intentionally tiny
    yaml = None

from runtime.aor.registry import _parse_simple_yaml


REQUIRED_WORKFLOW_IDS: tuple[str, ...] = (
    "chaseos_workflow_exchange",
    "growth_studio_proof_pack",
    "job_application_pack",
    "creator_content_to_market_batch",
    "tradesync_strikezone_supply_engine",
    "client_fulfillment_pipeline",
    "research_to_product_intelligence",
    "agent_runtime_governance_audit",
    "game_prototype_from_brief",
    "founder_automation_audit",
    "delegation_mesh",
    "university_portfolio_os",
    "ecommerce_reselling_ops",
    "ai_engineering_workflow_lab",
    "fullstack_build_to_proof_sprint",
)


def detect_vault_root() -> Path:
    here = Path(__file__).resolve()
    return here.parents[2]


def registry_path(vault_root: str | Path | None = None) -> Path:
    root = Path(vault_root).resolve() if vault_root is not None else detect_vault_root()
    return root / "runtime" / "workflows" / "registry" / "use_case_registry.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) if yaml is not None else _parse_simple_yaml(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse as a YAML mapping")
    return data


def load_use_case_registry(vault_root: str | Path | None = None) -> dict[str, Any]:
    path = registry_path(vault_root)
    if not path.exists():
        raise FileNotFoundError(path)
    return _load_yaml(path)


def workflow_records(registry: dict[str, Any]) -> list[dict[str, Any]]:
    records = registry.get("workflows")
    if records is None:
        records = registry.get("families")
    if not isinstance(records, list):
        raise ValueError("VentureOps registry must contain a workflows list")
    typed_records: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Every VentureOps registry record must be a mapping")
        typed_records.append(record)
    return typed_records


def workflow_by_id(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(record.get("workflow_id")): record for record in workflow_records(registry)}
