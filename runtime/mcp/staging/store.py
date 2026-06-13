"""Proposal artifact store for Runtime MCP V1.

Naming convention and artifact schema frozen against ChaseOS-MCP-Proposal-Staging.md v1.0.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from runtime.mcp.errors import MCPSystemError
from runtime.mcp.types import ProposalArtifact


class ProposalStore:
    """Store staged proposal artifacts under .chaseos/mcp-proposals/."""

    def __init__(self, staging_dir: Path) -> None:
        self.staging_dir = staging_dir

    def _filename_for(self, staged_at: str, proposal_id: str) -> str:
        """Compute {YYYYMMDD-HHMMSS}__{proposal_id[:8]}.json.

        staged_at is ISO 8601 UTC (e.g. '2026-04-20T11:30:42Z').
        """
        ts = staged_at[:19].replace("-", "").replace("T", "-").replace(":", "")
        # Strip "proposal-" prefix to get hex chars.
        _pid = proposal_id[9:] if proposal_id.startswith("proposal-") else proposal_id
        pid_short = _pid.replace("-", "")[:8] or proposal_id[:8]
        return f"{ts}__{pid_short}.json"

    def stage(self, artifact: ProposalArtifact) -> str:
        """Write artifact JSON to staging_dir. Return proposal_id.

        Raises MCPSystemError if write fails.
        Creates staging_dir if it does not exist.
        """
        filename = self._filename_for(artifact.staged_at, artifact.proposal_id)
        try:
            self.staging_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = self.staging_dir / f".{artifact.proposal_id}.tmp"
            final_path = self.staging_dir / filename
            tmp_path.write_text(
                json.dumps(artifact.to_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            tmp_path.replace(final_path)
        except Exception as exc:  # noqa: BLE001
            raise MCPSystemError(f"Failed to stage proposal: {exc}") from exc
        return artifact.proposal_id

    def _find_path(self, proposal_id: str) -> Path | None:
        """Locate a staged proposal file by proposal_id (searches JSON files)."""
        if not self.staging_dir.exists():
            return None
        for path in self.staging_dir.iterdir():
            if path.suffix != ".json" or path.name.startswith("."):
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if raw.get("proposal_id") == proposal_id:
                    return path
            except (json.JSONDecodeError, OSError):
                continue
        return None

    def read(self, proposal_id: str) -> ProposalArtifact | None:
        """Read and deserialize proposal by proposal_id.

        Returns None if not found. Caller decides policy.
        """
        path = self._find_path(proposal_id)
        if path is None:
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return ProposalArtifact(
                schema_version=raw.get("schema_version", "1.0"),
                proposal_id=raw["proposal_id"],
                staged_at=raw.get("staged_at", raw.get("created_at_utc", "")),
                runtime_id=raw["runtime_id"],
                safety_mode_at_staging=raw.get("safety_mode_at_staging", ""),
                change_type=raw.get("change_type", "update"),
                target_file=raw["target_file"],
                description=raw.get("description", raw.get("rationale", "")),
                proposed_content=raw.get("proposed_content"),
                current_sha256=raw.get("current_sha256"),
                proposed_sha256=raw.get("proposed_sha256"),
                governance_flags=dict(raw.get("governance_flags") or {}),
                status=raw.get("status", "staged"),
                status_history=list(raw.get("status_history") or []),
            )
        except Exception:  # noqa: BLE001
            return None

    def rollback(self, proposal_id: str) -> None:
        """Delete a just-staged proposal after proposal.submit audit failure.

        Raises MCPSystemError if rollback fails (non-recoverable inconsistency).
        """
        path = self._find_path(proposal_id)
        if path is None:
            return
        try:
            path.unlink()
        except Exception as exc:  # noqa: BLE001
            raise MCPSystemError(f"Rollback failed for {proposal_id}: {exc}") from exc

    def list_staged(self) -> list[str]:
        """Return list of proposal_id strings only. Returns [] if staging_dir missing."""
        if not self.staging_dir.exists():
            return []
        ids: list[str] = []
        for path in sorted(self.staging_dir.iterdir()):
            if path.suffix != ".json" or path.name.startswith("."):
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                pid = raw.get("proposal_id")
                if pid:
                    ids.append(str(pid))
            except (json.JSONDecodeError, OSError):
                continue
        return ids
