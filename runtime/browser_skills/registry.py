"""Registry helpers for Browser Operator Skill Layer skill files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback covers environments without PyYAML
    yaml = None

try:
    from runtime.aor.registry import _parse_simple_yaml as _parse_yaml_fallback
except Exception:  # pragma: no cover
    _parse_yaml_fallback = None


def detect_vault_root() -> Path:
    """Detect the ChaseOS vault root from this module path."""
    here = Path(__file__).resolve()
    vault_root = here.parents[2]
    if not (vault_root / "CLAUDE.md").exists():
        raise RuntimeError(f"Could not detect vault root from {here}")
    return vault_root


def skills_dir(vault_root: Path | None = None) -> Path:
    root = vault_root or detect_vault_root()
    return root / "runtime" / "browser_skills" / "skills"


def iter_skill_paths(vault_root: Path | None = None) -> list[Path]:
    """Return all YAML skill files under runtime/browser_skills/skills."""
    root = skills_dir(vault_root)
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.yaml")
        if path.is_file() and path.name.lower() != "readme.yaml"
    )


def load_yaml_file(path: Path | str) -> dict[str, Any]:
    """Load a YAML mapping from disk with a small fallback parser."""
    skill_path = Path(path)
    text = skill_path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
    elif _parse_yaml_fallback is not None:
        data = _parse_yaml_fallback(text)
    else:
        raise RuntimeError("PyYAML is unavailable and no fallback YAML parser is available")
    if not isinstance(data, dict):
        raise ValueError(f"Skill file did not parse as a mapping: {skill_path}")
    return data


def load_skill(skill_id: str, vault_root: Path | None = None) -> dict[str, Any] | None:
    """Load a skill by skill_id, returning None when not found."""
    for path in iter_skill_paths(vault_root):
        data = load_yaml_file(path)
        if data.get("skill_id") == skill_id:
            data = dict(data)
            data["_path"] = str(path)
            return data
    return None


def list_skills(vault_root: Path | None = None) -> list[dict[str, Any]]:
    """Return lightweight records for all registered browser skills."""
    records: list[dict[str, Any]] = []
    for path in iter_skill_paths(vault_root):
        data = load_yaml_file(path)
        records.append(
            {
                "skill_id": data.get("skill_id"),
                "domain": data.get("domain"),
                "intent": data.get("intent"),
                "status": data.get("status"),
                "mode": data.get("mode"),
                "approval_status": data.get("approval_status"),
                "risk_level": data.get("risk_level"),
                "last_verified": data.get("last_verified"),
                "path": str(path),
            }
        )
    return records
