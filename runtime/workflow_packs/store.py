"""Local JSON store for WorkflowPack runs, artifacts, gates, and proof cards."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from .models import (
    ApprovalActionType,
    ApprovalGate,
    ApprovalReference,
    ArtifactReference,
    ArtifactType,
    ReviewStatus,
    RiskFlag,
    RuntimeReference,
    SourceReference,
    WorkflowArtifact,
    WorkflowRun,
    WorkflowRunStatus,
    utc_now,
)
from .registry import get_workflow_pack


STATE_ROOT = Path("runtime/workflow_packs/state")


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "workflow-pack"


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _artifact_ref_from_dict(data: dict[str, Any]) -> ArtifactReference:
    return ArtifactReference(
        id=str(data.get("id", "")),
        local_path=str(data.get("local_path", "")),
        title=str(data.get("title", "")),
        artifact_type=data.get("artifact_type", "markdown"),
        review_status=data.get("review_status", "pending_review"),
    )


def _source_ref_from_dict(data: dict[str, Any]) -> SourceReference:
    return SourceReference(
        id=str(data.get("id", "")),
        source_type=str(data.get("source_type", "manual_note")),
        captured_at=str(data.get("captured_at", utc_now())),
        provenance_status=str(data.get("provenance_status", "candidate")),
        sensitivity_status=str(data.get("sensitivity_status", "unknown")),
        uri=str(data.get("uri", "")),
        local_path=str(data.get("local_path", "")),
        title=str(data.get("title", "")),
        summary=str(data.get("summary", "")),
    )


def _runtime_ref_from_dict(data: dict[str, Any]) -> RuntimeReference:
    return RuntimeReference(
        id=str(data.get("id", "")),
        runtime=str(data.get("runtime", "")),
        mode=str(data.get("mode", "")),
        summary=str(data.get("summary", "")),
    )


def _approval_ref_from_dict(data: dict[str, Any]) -> ApprovalReference:
    return ApprovalReference(
        id=str(data.get("id", "")),
        action_type=data.get("action_type", "external_api_call"),
        status=data.get("status", "pending"),
        reason=str(data.get("reason", "")),
    )


def _risk_flag_from_dict(data: dict[str, Any]) -> RiskFlag:
    return RiskFlag(
        id=str(data.get("id", "")),
        severity=str(data.get("severity", "medium")),
        summary=str(data.get("summary", "")),
        blocked=bool(data.get("blocked", False)),
    )


def workflow_run_from_dict(data: dict[str, Any]) -> WorkflowRun:
    return WorkflowRun(
        id=str(data.get("id", "")),
        pack_id=str(data.get("pack_id", "")),
        title=str(data.get("title", "")),
        status=data.get("status", "created"),
        input=dict(data.get("input") or {}),
        source_refs=[_source_ref_from_dict(item) for item in data.get("source_refs", [])],
        runtime_refs=[_runtime_ref_from_dict(item) for item in data.get("runtime_refs", [])],
        approval_refs=[_approval_ref_from_dict(item) for item in data.get("approval_refs", [])],
        artifact_refs=[_artifact_ref_from_dict(item) for item in data.get("artifact_refs", [])],
        risk_flags=[_risk_flag_from_dict(item) for item in data.get("risk_flags", [])],
        created_at=str(data.get("created_at", utc_now())),
        updated_at=str(data.get("updated_at", utc_now())),
        proof_card_id=str(data.get("proof_card_id", "")),
        audit_log_ref=str(data.get("audit_log_ref", "")),
        provider_mode=str(data.get("provider_mode", "demo_manual")),
    )


class WorkflowPackStore:
    """Create-only local storage for workflow-pack MVP run artifacts."""

    def __init__(self, vault_root: str | Path) -> None:
        self.vault_root = Path(vault_root).resolve()
        self.state_root = self.vault_root / STATE_ROOT
        self.runs_root = self.state_root / "runs"

    def _relative(self, path: Path) -> str:
        resolved = path.resolve()
        if not resolved.is_relative_to(self.vault_root):
            raise ValueError(f"path escapes vault root: {path}")
        return resolved.relative_to(self.vault_root).as_posix()

    def run_dir(self, run_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", run_id):
            raise ValueError("invalid run id")
        return self.runs_root / run_id

    def run_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "run.json"

    def list_runs(self) -> list[WorkflowRun]:
        if not self.runs_root.exists():
            return []
        runs: list[WorkflowRun] = []
        for path in sorted(self.runs_root.glob("*/run.json")):
            runs.append(workflow_run_from_dict(_read_json(path)))
        return sorted(runs, key=lambda run: run.created_at, reverse=True)

    def get_run(self, run_id: str) -> WorkflowRun:
        path = self.run_path(run_id)
        if not path.exists():
            raise FileNotFoundError(path)
        return workflow_run_from_dict(_read_json(path))

    def save_run(self, run: WorkflowRun) -> WorkflowRun:
        updated = replace(run, updated_at=utc_now())
        _write_json(self.run_path(updated.id), updated.to_dict())
        return updated

    def create_run(
        self,
        *,
        pack_id: str,
        title: str,
        user_goal: str,
        input_data: dict[str, Any] | None = None,
        source_refs: list[SourceReference] | None = None,
        status: WorkflowRunStatus = "created",
    ) -> WorkflowRun:
        pack = get_workflow_pack(pack_id)
        now = utc_now()
        run_id = f"{now.replace(':', '').replace('-', '').replace('.', '')[:15]}-{_slug(pack.id)}-{uuid.uuid4().hex[:8]}"
        audit_log = self.run_dir(run_id) / "audit_log.jsonl"
        run = WorkflowRun(
            id=run_id,
            pack_id=pack.id,
            title=title.strip() or f"{pack.name} demo run",
            status=status,
            input={"user_goal": user_goal.strip(), **(input_data or {})},
            source_refs=source_refs or [],
            runtime_refs=[
                RuntimeReference(
                    id="manual-provider-demo",
                    runtime="manual_provider",
                    mode="demo_manual",
                    summary="Local deterministic demo provider; no external integration or model call.",
                )
            ],
            approval_refs=[],
            artifact_refs=[],
            risk_flags=[
                RiskFlag(
                    id="demo_manual_provider",
                    severity="info",
                    summary="Run created in demo/manual provider mode.",
                    blocked=False,
                )
            ],
            created_at=now,
            updated_at=now,
            audit_log_ref=self._relative(audit_log),
            provider_mode="demo_manual",
        )
        self.run_dir(run_id).mkdir(parents=True, exist_ok=True)
        audit_log.write_text(json.dumps({"event": "run_created", "at": now, "pack_id": pack.id}) + "\n", encoding="utf-8")
        return self.save_run(run)

    def append_audit_event(self, run_id: str, event: str, data: dict[str, Any] | None = None) -> None:
        run = self.get_run(run_id)
        event_record = {
            "event": event,
            "at": utc_now(),
            "run_id": run_id,
            "pack_id": run.pack_id,
            "data": data or {},
        }
        audit_path = self.vault_root / run.audit_log_ref
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        with audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event_record, sort_keys=True) + "\n")

    def create_artifact(
        self,
        *,
        run_id: str,
        artifact_type: ArtifactType,
        title: str,
        content: str,
        extension: str = "md",
        mime_type: str = "text/markdown",
        created_by: str = "local_service",
        review_status: ReviewStatus = "pending_review",
        public_share_safe: bool = False,
    ) -> WorkflowArtifact:
        run = self.get_run(run_id)
        artifact_id = f"artifact-{uuid.uuid4().hex[:12]}"
        safe_ext = extension.lstrip(".") or "md"
        artifact_path = self.run_dir(run_id) / "artifacts" / f"{artifact_id}.{safe_ext}"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(content, encoding="utf-8")
        artifact = WorkflowArtifact(
            id=artifact_id,
            run_id=run_id,
            artifact_type=artifact_type,
            title=title,
            local_path=self._relative(artifact_path),
            mime_type=mime_type,
            created_at=utc_now(),
            created_by=created_by,
            review_status=review_status,
            public_share_safe=public_share_safe,
        )
        _write_json(artifact_path.with_suffix(artifact_path.suffix + ".json"), artifact.to_dict())
        ref = ArtifactReference(
            id=artifact.id,
            local_path=artifact.local_path,
            title=artifact.title,
            artifact_type=artifact.artifact_type,
            review_status=artifact.review_status,
        )
        self.save_run(
            replace(
                run,
                status="artifact_ready",
                artifact_refs=[*run.artifact_refs, ref],
            )
        )
        return artifact

    def list_artifacts(self, run_id: str) -> list[WorkflowArtifact]:
        run_dir = self.run_dir(run_id) / "artifacts"
        if not run_dir.exists():
            return []
        artifacts: list[WorkflowArtifact] = []
        for path in sorted(run_dir.glob("*.json")):
            data = _read_json(path)
            if data.get("run_id") != run_id or not data.get("id"):
                continue
            artifacts.append(
                WorkflowArtifact(
                    id=str(data.get("id", "")),
                    run_id=str(data.get("run_id", run_id)),
                    artifact_type=data.get("artifact_type", "markdown"),
                    title=str(data.get("title", "")),
                    local_path=str(data.get("local_path", "")),
                    mime_type=str(data.get("mime_type", "")),
                    created_at=str(data.get("created_at", "")),
                    created_by=str(data.get("created_by", "")),
                    review_status=data.get("review_status", "pending_review"),
                    public_share_safe=bool(data.get("public_share_safe", False)),
                )
            )
        return artifacts

    def create_approval_gate(
        self,
        *,
        run_id: str,
        action_type: ApprovalActionType,
        reason: str,
        preview_artifact_refs: list[str] | None = None,
        requested_by: str = "workflow_packs_demo_provider",
    ) -> ApprovalGate:
        run = self.get_run(run_id)
        gate_id = f"gate-{uuid.uuid4().hex[:12]}"
        risk = RiskFlag(
            id=f"{action_type}_requires_human_approval",
            severity="high",
            summary=f"{action_type} is blocked until a human approval path exists for this run.",
            blocked=True,
        )
        gate = ApprovalGate(
            id=gate_id,
            run_id=run_id,
            action_type=action_type,
            status="pending",
            requested_by=requested_by,
            requested_at=utc_now(),
            reason=reason,
            preview_artifact_refs=preview_artifact_refs or [],
            risk_flags=[risk],
        )
        gate_path = self.run_dir(run_id) / "approvals" / f"{gate_id}.json"
        _write_json(gate_path, gate.to_dict())
        self.save_run(
            replace(
                run,
                status="approval_required",
                approval_refs=[
                    *run.approval_refs,
                    ApprovalReference(
                        id=gate.id,
                        action_type=gate.action_type,
                        status=gate.status,
                        reason=gate.reason,
                    ),
                ],
                risk_flags=[*run.risk_flags, risk],
            )
        )
        return gate

    def approval_gate_path(self, run_id: str, gate_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", gate_id):
            raise ValueError("invalid gate id")
        return self.run_dir(run_id) / "approvals" / f"{gate_id}.json"

    def save_approval_gate(self, gate: ApprovalGate) -> ApprovalGate:
        _write_json(self.approval_gate_path(gate.run_id, gate.id), gate.to_dict())
        return gate

    def list_approval_gates(self, run_id: str) -> list[ApprovalGate]:
        gates_dir = self.run_dir(run_id) / "approvals"
        if not gates_dir.exists():
            return []
        gates: list[ApprovalGate] = []
        for path in sorted(gates_dir.glob("*.json")):
            data = _read_json(path)
            gates.append(
                ApprovalGate(
                    id=str(data.get("id", "")),
                    run_id=str(data.get("run_id", run_id)),
                    action_type=data.get("action_type", "external_api_call"),
                    status=data.get("status", "pending"),
                    requested_by=str(data.get("requested_by", "")),
                    requested_at=str(data.get("requested_at", "")),
                    reason=str(data.get("reason", "")),
                    preview_artifact_refs=list(data.get("preview_artifact_refs") or []),
                    risk_flags=[_risk_flag_from_dict(item) for item in data.get("risk_flags", [])],
                    approved_by=str(data.get("approved_by", "")),
                    approved_at=str(data.get("approved_at", "")),
                )
            )
        return gates

    def save_proof_card(self, *, run_id: str, proof_card: dict[str, Any], markdown: str) -> dict[str, str]:
        run = self.get_run(run_id)
        proof_dir = self.run_dir(run_id) / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)
        json_path = proof_dir / "proof_card.json"
        markdown_path = proof_dir / "proof_card.md"
        _write_json(json_path, proof_card)
        markdown_path.write_text(markdown, encoding="utf-8")
        ref = ArtifactReference(
            id=str(proof_card["id"]),
            local_path=self._relative(markdown_path),
            title=str(proof_card["title"]),
            artifact_type="proof_card",
            review_status="pending_review",
        )
        existing = [item for item in run.artifact_refs if item.id != ref.id]
        self.save_run(
            replace(
                run,
                status="review_required",
                proof_card_id=str(proof_card["id"]),
                artifact_refs=[*existing, ref],
            )
        )
        return {
            "proof_card_json_path": self._relative(json_path),
            "proof_card_markdown_path": self._relative(markdown_path),
        }
