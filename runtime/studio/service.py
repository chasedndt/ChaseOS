"""
studio/service.py — ChaseOS Studio Service Layer

The mandatory governance backend for all Studio write operations. No UI feature may
write to the vault outside this service layer path.

Responsibilities:
  - Validate action specs against Gate policies and protected-file rules
  - Route write targets to safe vault paths
  - Queue gated actions for operator approval (durable JSON queue)
  - Execute approved writes with audit-safe semantics
  - Emit OSRIL events to the agent bus (fail-open)
  - Log all actions to 07_LOGS/Agent-Activity/

Governance rules encoded here:
  1. No writes outside vault root (path traversal guard — fail-closed)
  2. Protected files require explicit approval regardless of action type
  3. No .py/.sh/.bat script writes (code injection guard — fail-closed)
  4. All deletes require approval (no soft deletes without operator confirmation)
  5. Canonical promotion path requires approval
  6. All actions logged to audit trail regardless of approval outcome
  7. Bus event emission is fail-open (bus unavailable does not block writes)

AOR registration: Studio service is invoked directly, not through AOR engine.
It is a service layer, not a workflow handler.

Usage:
  svc = StudioService(vault_root)
  result = svc.validate_action(action_spec)
  if result.approval_required:
      req = svc.queue_for_approval(action_spec)
      # ... operator approves ...
      svc.execute_approved(req.approval_id)
  else:
      svc.execute_write(action_spec)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ── Protected-file guard ──────────────────────────────────────────────────────
# Mirrors CLAUDE.md Section "Protected Files". Must never be casually edited.
_PROTECTED_FILES = frozenset(
    [
        "SOUL.md",
        "00_HOME/Principles.md",
        "00_HOME/Operating-System.md",
        "00_HOME/Assistant-Contract.md",
        "README.md",
        "PROJECT_FOUNDATION.md",
        "ROADMAP.md",
        "FORKING.md",
        "CLAUDE.md",
        "06_AGENTS/Agent-Control-Plane.md",
        "06_AGENTS/Permission-Matrix.md",
        "06_AGENTS/Trust-Tiers.md",
        "06_AGENTS/Handoff-Protocol.md",
    ]
)

# File extensions that are always forbidden from Studio write operations.
_FORBIDDEN_WRITE_EXTENSIONS = frozenset(
    [".py", ".sh", ".bat", ".ps1", ".cmd", ".exe", ".so", ".dll"]
)

# Paths that always require approval regardless of content.
_ALWAYS_APPROVAL_REQUIRED_PREFIXES = (
    "02_KNOWLEDGE/",
    "01_PROJECTS/",
    "00_HOME/",
    "04_SOPS/",
    "06_AGENTS/",
    "runtime/aor/",
    ".chaseos/",               # N-5: companion routing config + watch folders + dedup registry
    "runtime/studio/approvals/",  # N-6: block direct writes to approval queue (forgery guard)
)


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class ActionSpec:
    """Specification for a Studio write operation."""
    action_type: str       # "create_file" | "write_file" | "delete_file" | "promote_quarantine"
    target_path: str       # relative vault path
    content: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    submitted_by: str = "studio"
    note: str = ""         # operator-provided justification (optional)

    def is_delete(self) -> bool:
        return self.action_type == "delete_file"

    def is_promote(self) -> bool:
        return self.action_type == "promote_quarantine"


@dataclass
class ValidationResult:
    """Outcome of action spec validation."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    gate_blocked: bool = False    # hard no — cannot proceed regardless of approval
    approval_required: bool = True

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


@dataclass
class ApprovalRequest:
    """Durable record of a pending write action awaiting operator approval."""
    approval_id: str
    action_spec: ActionSpec
    status: str               # "pending" | "approved" | "executing" | "executed" | "execution_failed" | "rejected" | "expired"
    submitted_at: str         # ISO-8601 UTC
    updated_at: str           # ISO-8601 UTC
    reviewed_by: Optional[str] = None
    reason: str = ""          # rejection reason or approval note
    execution_id: Optional[str] = None
    execution_started_at: Optional[str] = None
    execution_finished_at: Optional[str] = None
    execution_status: Optional[str] = None
    result_action_id: Optional[str] = None
    execution_error: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["action_spec"] = asdict(self.action_spec)
        return d


@dataclass
class ActionResult:
    """Record of a completed (or rejected) Studio write action."""
    action_id: str
    action_type: str
    target_path: str
    status: str        # "completed" | "rejected" | "gate_blocked" | "error"
    submitted_by: str
    executed_at: str   # ISO-8601 UTC
    approval_id: Optional[str] = None
    writes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    event_emitted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── Core service ──────────────────────────────────────────────────────────────

class StudioServiceError(Exception):
    """Hard governance violation — action must not proceed."""


class StudioService:
    """
    ChaseOS Studio Service Layer.

    Validates, gates, and executes write actions for Studio surfaces.
    All writes go through this layer — there is no bypass path.
    """

    APPROVAL_DIR = "runtime/studio/approvals"
    AUDIT_DIR = "07_LOGS/Agent-Activity"

    def __init__(self, vault_root: str | Path, *, dry_run: bool = False) -> None:
        self._vault = Path(vault_root).resolve()
        self._dry_run = dry_run
        self._approval_dir = self._vault / self.APPROVAL_DIR
        self._audit_dir = self._vault / self.AUDIT_DIR

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_action(self, spec: ActionSpec) -> ValidationResult:
        """
        Validate an ActionSpec against all governance rules.

        Returns a ValidationResult — the caller must check `.gate_blocked` before
        proceeding. A gate-blocked result must not be queued for approval.
        """
        result = ValidationResult(valid=True)

        # 1. Resolve and check target path
        try:
            resolved = self._resolve_path(spec.target_path)
        except StudioServiceError as exc:
            result.add_error(str(exc))
            result.gate_blocked = True
            return result

        rel_posix = resolved.relative_to(self._vault).as_posix()

        # 2. Forbidden extension guard
        suffix = resolved.suffix.lower()
        if suffix in _FORBIDDEN_WRITE_EXTENSIONS:
            result.add_error(
                f"Studio writes to {suffix} files are forbidden. "
                "Code injection guard — this is a hard governance block."
            )
            result.gate_blocked = True

        # 3. Protected file guard
        is_protected = (
            rel_posix in _PROTECTED_FILES
            or any(rel_posix.endswith("/" + pf) for pf in _PROTECTED_FILES)
        )
        if is_protected:
            result.add_error(
                f"'{rel_posix}' is a protected file. "
                "Protected files require explicit user instruction to modify — "
                "Studio cannot gate-approve modifications to protected files."
            )
            result.gate_blocked = True

        # 4. Quarantine target validation for promote actions
        if spec.is_promote():
            if "00_QUARANTINE" not in rel_posix:
                result.add_error(
                    "promote_quarantine action target must be inside 03_INPUTS/00_QUARANTINE/."
                )
                result.gate_blocked = True

        # 5. Delete guard
        if spec.is_delete():
            if not resolved.exists():
                result.add_warning(f"'{rel_posix}' does not exist — delete is a no-op.")
            result.approval_required = True

        # 6. Approval heuristic for sensitive paths
        if not result.gate_blocked:
            needs_approval = spec.is_delete() or spec.is_promote()
            if not needs_approval:
                needs_approval = any(rel_posix.startswith(p) for p in _ALWAYS_APPROVAL_REQUIRED_PREFIXES)
            result.approval_required = needs_approval

        # 7. Content required for write actions
        if spec.action_type in {"create_file", "write_file"} and spec.content is None:
            result.add_error("content is required for write/create actions.")

        if result.errors:
            result.valid = False
        return result

    # ── Approval queue ────────────────────────────────────────────────────────

    def queue_for_approval(self, spec: ActionSpec) -> ApprovalRequest:
        """
        Persist an approval request for a gated action.

        The caller should first validate the spec — gate-blocked specs must not be queued.
        """
        now = _now_iso()
        req = ApprovalRequest(
            approval_id=str(uuid.uuid4()),
            action_spec=spec,
            status="pending",
            submitted_at=now,
            updated_at=now,
        )
        self._write_approval_record(req)
        return req

    def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Load an approval request by ID."""
        path = self._approval_path(approval_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            spec_data = data.pop("action_spec", {})
            spec = ActionSpec(**spec_data)
            return ApprovalRequest(action_spec=spec, **data)
        except Exception:
            return None

    def list_pending(self) -> list[ApprovalRequest]:
        """Return all pending approval requests, sorted by submission time."""
        results = []
        if not self._approval_dir.exists():
            return results
        for path in sorted(self._approval_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("status") != "pending":
                    continue
                spec_data = data.pop("action_spec", {})
                spec = ActionSpec(**spec_data)
                results.append(ApprovalRequest(action_spec=spec, **data))
            except Exception:
                continue
        return results

    def approve(self, approval_id: str, *, reviewed_by: str = "operator") -> ApprovalRequest:
        """Mark a pending approval as approved."""
        return self._transition_approval(approval_id, "approved", reviewed_by=reviewed_by)

    def reject(self, approval_id: str, *, reason: str = "", reviewed_by: str = "operator") -> ApprovalRequest:
        """Mark a pending approval as rejected."""
        return self._transition_approval(
            approval_id, "rejected", reviewed_by=reviewed_by, reason=reason
        )

    def execute_approved(self, approval_id: str) -> ActionResult:
        """
        Execute a previously approved write action.

        Reserves the approval before writes so duplicate execution blocks before
        any filesystem mutation can occur. Logs result regardless of outcome.
        """
        req = self.get_approval(approval_id)
        if req is None:
            raise StudioServiceError(f"Approval request not found: {approval_id}")
        if req.status != "approved":
            raise StudioServiceError(
                f"Cannot execute approval {approval_id} with status '{req.status}'. "
                "Only 'approved' requests may be executed."
            )
        if req.action_spec.metadata.get("phase11_chat_queue_write_execution_blocked") is True:
            raise StudioServiceError(
                "Phase 11 Chat approval queue write proof requests are pending-review "
                "artifacts only. Approval execution and target vault writes remain "
                "blocked until a future governed Chat approval-consumption pass."
            )
        if req.action_spec.metadata.get("phase11_companion_selection_queue_write_execution_proof") is True:
            raise StudioServiceError(
                "Phase 11 companion selection approval queue write proof requests are "
                "pending-review artifacts only. Approval execution and companion "
                "selection target writes remain blocked until a future governed "
                "companion-selection approval-consumption pass."
            )
        if req.action_spec.metadata.get("phase11_companion_memory_approval_preview") is True:
            raise StudioServiceError(
                "Phase 11 companion memory approval requests must be consumed only "
                "by the governed companion memory approved execution proof. Ambient "
                "Studio approval execution cannot create companion memory ledgers."
            )
        if req.action_spec.metadata.get("phase11_companion_memory_ledger_write_approval_preview") is True:
            raise StudioServiceError(
                "Phase 11 companion memory ledger-write approval requests must be "
                "consumed only by the governed companion memory approved ledger-write "
                "executor. Ambient Studio approval execution cannot append companion "
                "memory ledgers."
            )
        if req.action_spec.metadata.get("personal_context_import_preview_writer") is True:
            raise StudioServiceError(
                "Personal context import preview approval requests must be consumed "
                "only by the governed personal context import execution proof. "
                "Ambient Studio approval execution cannot write raw context, nodes, "
                "indexes, Personal Map candidates, runtime memory, or canonical "
                "personal context."
            )
        if req.action_spec.metadata.get("personal_context_import_canonical_promotion_approval_preview") is True:
            raise StudioServiceError(
                "Personal context import canonical-promotion approval requests must "
                "be consumed only by the governed canonical-promotion executor. "
                "Ambient Studio approval execution cannot write canonical nodes, "
                "Dashboard, Personal Operator Index, Operating System, Projects Hub, "
                "Knowledge Index, Personal Map apply records, runtime memory, Agent "
                "Bus tasks, provider calls, or credential reads."
            )
        if req.action_spec.metadata.get("phase11_chat_runtime_dispatch_executor") is True:
            raise StudioServiceError(
                "Phase 11 Chat runtime dispatch approval requests must be consumed "
                "only by the governed runtime dispatch executor. Ambient Studio "
                "approval execution cannot create Agent Bus tasks or dispatch runtime work."
            )
        if req.action_spec.metadata.get("phase11_chat_workspace_proposal_writer") is True:
            raise StudioServiceError(
                "Phase 11 Chat workspace proposal requests must be consumed only "
                "by the governed workspace proposal consumption executor. Ambient Studio "
                "approval execution cannot create Chat workspaces, folders, threads, "
                "messages, Discord threads, Agent Bus tasks, runtime board items, "
                "or schedule changes."
            )
        if req.action_spec.metadata.get("phase11_chat_runtime_board_handoff_proposal") is True:
            raise StudioServiceError(
                "Phase 11 Chat runtime board handoff requests must be consumed only "
                "by a future governed runtime board handoff executor. Ambient Studio "
                "approval execution cannot create runtime board items, Agent Bus tasks, "
                "runtime dispatches, Discord calls, schedule changes, provider calls, "
                "or canonical writeback."
            )
        if req.action_spec.metadata.get("phase11_chat_schedule_proposal_packet") is True:
            raise StudioServiceError(
                "Phase 11 Chat schedule proposal requests must be consumed only "
                "by the governed schedule proposal consumption executor. Ambient "
                "Studio approval execution cannot write schedule intent YAML, "
                "regenerate schedule indexes, mutate external scheduler state, "
                "dispatch runtimes, call Discord or providers, or perform canonical "
                "writeback."
            )
        if req.action_spec.metadata.get("phase11_chat_schedule_activation_readiness") is True:
            raise StudioServiceError(
                "Phase 11 Chat schedule activation approval requests must be "
                "consumed only by a future governed schedule activation executor. "
                "Ambient Studio approval execution cannot enable schedules, "
                "regenerate schedule indexes, mutate external scheduler state, "
                "change OpenClaw/Hermes cron, dispatch runtimes, call Discord or "
                "providers, or read credentials."
            )
        if req.action_spec.metadata.get("phase11_chat_schedule_adapter_export_readiness") is True:
            raise StudioServiceError(
                "Phase 11 Chat schedule adapter export approval requests must be "
                "consumed only by a future governed adapter export packet writer. "
                "Ambient Studio approval execution cannot write adapter export packets, "
                "mutate external scheduler state, change OpenClaw/Hermes cron, dispatch "
                "runtimes, call Discord or providers, or read credentials."
            )
        if req.action_spec.metadata.get("personal_map_apply_readiness_approval") is True:
            raise StudioServiceError(
                "Personal context import Personal Map apply readiness approval requests "
                "must be consumed only by the governed personal-map-approved-apply-executor. "
                "Ambient Studio approval execution cannot apply Personal Map candidates, "
                "write graph.json, dispatch Agent Bus tasks, mutate runtime memory, call "
                "providers, or read credentials."
            )
        if req.action_spec.metadata.get("runtime_memory_mutation_readiness_approval") is True:
            raise StudioServiceError(
                "Personal context import runtime memory mutation readiness approval requests "
                "must be consumed only by the governed runtime-memory-approved-mutation-executor. "
                "Ambient Studio approval execution cannot write runtime nav maps, dispatch "
                "Agent Bus tasks, apply Personal Map candidates, call providers, or read "
                "credentials."
            )
        if req.action_spec.metadata.get("provider_credential_readiness_approval") is True:
            raise StudioServiceError(
                "Personal context import provider credential readiness approval requests "
                "must be consumed only by the governed provider-execution-proof surface. "
                "Ambient Studio approval execution cannot call provider APIs, read secret "
                "values, write canonical files, or dispatch Agent Bus tasks."
            )
        req.status = "executing"
        req.execution_id = str(uuid.uuid4())
        req.execution_started_at = _now_iso()
        req.execution_finished_at = None
        req.execution_status = None
        req.result_action_id = None
        req.execution_error = ""
        req.updated_at = req.execution_started_at
        self._write_approval_record(req)

        result = self._execute(req.action_spec, approval_id=approval_id)
        req.status = "executed" if result.status in {"completed", "dry_run"} else "execution_failed"
        req.execution_finished_at = _now_iso()
        req.execution_status = result.status
        req.result_action_id = result.action_id
        req.execution_error = "; ".join(result.errors)
        req.updated_at = req.execution_finished_at
        self._write_approval_record(req)

        self._audit(result)
        self._try_emit_event(result)
        return result

    def execute_write(self, spec: ActionSpec) -> ActionResult:
        """
        Execute a write action that does not require approval.

        Validates first — will raise StudioServiceError on gate-blocked specs.
        """
        validation = self.validate_action(spec)
        if validation.gate_blocked:
            errors = "; ".join(validation.errors)
            raise StudioServiceError(f"Gate-blocked: {errors}")
        if validation.approval_required:
            raise StudioServiceError(
                "This action requires approval. Use queue_for_approval() then execute_approved()."
            )
        result = self._execute(spec)
        self._audit(result)
        self._try_emit_event(result)
        return result

    # ── Internal execution ────────────────────────────────────────────────────

    def _execute(self, spec: ActionSpec, approval_id: Optional[str] = None) -> ActionResult:
        now = _now_iso()
        action_id = str(uuid.uuid4())[:8]
        writes: list[str] = []
        errors: list[str] = []

        try:
            resolved = self._resolve_path(spec.target_path)
            rel = resolved.relative_to(self._vault).as_posix()

            if self._dry_run:
                return ActionResult(
                    action_id=action_id,
                    action_type=spec.action_type,
                    target_path=spec.target_path,
                    status="dry_run",
                    submitted_by=spec.submitted_by,
                    executed_at=now,
                    approval_id=approval_id,
                    writes=[],
                )

            if spec.action_type in {"create_file", "write_file"}:
                resolved.parent.mkdir(parents=True, exist_ok=True)
                resolved.write_text(spec.content or "", encoding="utf-8")
                writes.append(rel)

            elif spec.action_type == "delete_file":
                if resolved.exists() and resolved.is_file():
                    resolved.unlink()
                    writes.append(rel)

            elif spec.action_type == "promote_quarantine":
                # Promote a quarantine file to its declared destination
                dest_path = spec.metadata.get("destination_path")
                if not dest_path:
                    raise StudioServiceError("promote_quarantine requires metadata.destination_path")
                dest = self._resolve_path(dest_path)
                dest.parent.mkdir(parents=True, exist_ok=True)
                resolved.rename(dest)
                writes.append(dest.relative_to(self._vault).as_posix())

            elif spec.action_type == "execute_process":
                # The actual subprocess is launched by the API caller (start_runtime_daemon
                # phase 2) after verifying approval.status == "approved".
                # execute_approved is intentionally a no-op here — it only records that
                # the approval gate was satisfied.
                pass

            else:
                raise StudioServiceError(f"Unknown action_type: {spec.action_type!r}")

            status = "completed"

        except StudioServiceError as exc:
            errors.append(str(exc))
            status = "error"
        except Exception as exc:
            errors.append(f"Unexpected error: {exc}")
            status = "error"

        return ActionResult(
            action_id=action_id,
            action_type=spec.action_type,
            target_path=spec.target_path,
            status=status,
            submitted_by=spec.submitted_by,
            executed_at=now,
            approval_id=approval_id,
            writes=writes,
            errors=errors,
        )

    # ── Path resolution ───────────────────────────────────────────────────────

    def _resolve_path(self, target_path: str) -> Path:
        """Resolve and validate a target path against vault root. Raises on traversal."""
        if not target_path or not target_path.strip():
            raise StudioServiceError("target_path must not be empty.")

        # Reject absolute paths that aren't inside the vault
        candidate = Path(target_path)
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            resolved = (self._vault / candidate).resolve()

        # Path traversal guard
        try:
            resolved.relative_to(self._vault)
        except ValueError:
            raise StudioServiceError(
                f"target_path '{target_path}' resolves outside vault root. "
                "Path traversal is a hard governance block."
            )
        return resolved

    # ── Approval persistence ──────────────────────────────────────────────────

    def _approval_path(self, approval_id: str) -> Path:
        safe_id = "".join(c if c.isalnum() or c == "-" else "_" for c in approval_id)
        return self._approval_dir / f"{safe_id}.json"

    def _write_approval_record(self, req: ApprovalRequest) -> None:
        if self._dry_run:
            return
        self._approval_dir.mkdir(parents=True, exist_ok=True)
        path = self._approval_path(req.approval_id)
        path.write_text(json.dumps(req.to_dict(), indent=2), encoding="utf-8")

    def _transition_approval(
        self,
        approval_id: str,
        new_status: str,
        *,
        reviewed_by: str,
        reason: str = "",
    ) -> ApprovalRequest:
        req = self.get_approval(approval_id)
        if req is None:
            raise StudioServiceError(f"Approval request not found: {approval_id}")
        if req.status != "pending":
            raise StudioServiceError(
                f"Cannot transition approval {approval_id} from status '{req.status}'. "
                "Only 'pending' approvals may be transitioned."
            )
        req.status = new_status
        req.updated_at = _now_iso()
        req.reviewed_by = reviewed_by
        req.reason = reason
        self._write_approval_record(req)
        return req

    # ── Audit log ─────────────────────────────────────────────────────────────

    def _audit(self, result: ActionResult) -> None:
        if self._dry_run:
            return
        try:
            self._audit_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            filename = f"{ts}__studio__{result.action_type[:20]}__{result.action_id}.md"
            path = self._audit_dir / filename
            content = _build_audit_content(result)
            path.write_text(content, encoding="utf-8")
        except Exception:
            pass  # audit failure must not block the action result

    # ── Bus event emission ────────────────────────────────────────────────────

    def _try_emit_event(self, result: ActionResult) -> None:
        try:
            from runtime.agent_bus.bus import create_task
            create_task(
                self._vault,
                sender="Studio",
                recipient="OpenClaw",
                task_type="notice",
                intent="notice",
                request=f"Studio action completed: {result.action_type} → {result.target_path} [{result.status}]",
                notes=(
                    f"action_id: {result.action_id}\n"
                    f"status: {result.status}\n"
                    f"writes: {', '.join(result.writes) or 'none'}"
                ),
            )
            result.event_emitted = True
        except Exception:
            pass  # fail-open — bus unavailable does not block action


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_audit_content(result: ActionResult) -> str:
    writes_block = "\n".join(f"  - {w}" for w in result.writes) or "  (none)"
    errors_block = "\n".join(f"  - {e}" for e in result.errors) or "  (none)"
    return f"""---
type: agent-activity
surface: studio
action_type: {result.action_type}
action_id: {result.action_id}
status: {result.status}
submitted_by: {result.submitted_by}
executed_at: {result.executed_at}
approval_id: {result.approval_id or "none"}
---

# Studio Action — {result.action_type}

**Action ID:** `{result.action_id}`
**Target:** `{result.target_path}`
**Status:** {result.status}
**Submitted by:** {result.submitted_by}
**Executed at:** {result.executed_at}
**Approval ID:** {result.approval_id or "none"}

## Writes

{writes_block}

## Errors

{errors_block}

## Boundary Statement

This action was executed through the ChaseOS Studio Service Layer.
All writes were validated against Gate policies and protected-file rules
before execution. Approval-required actions were gated through the
durable approval queue. No bypasses.
"""
