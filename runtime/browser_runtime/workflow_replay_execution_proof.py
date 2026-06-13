"""Bounded safe-local Browser Workflow replay execution proof.

This module executes one reviewed local workflow replay only after the
approval/idempotency contract is ready. It writes a create-new approval record
and reserves the idempotency marker before any browser controller opens the
target. The default live controller uses the existing throwaway-profile CDP
launcher; tests inject a fake controller so ordering and artifact writes are
verified without requiring a local browser install.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from runtime.browser_runtime.models import domain_from_url, slugify
from runtime.browser_runtime.workflow_replay_execution_approval import (
    WORKFLOW_REPLAY_EXECUTION_APPROVAL_READY,
    WorkflowReplayExecutionApprovalRequest,
    build_workflow_replay_execution_approval,
)
from runtime.browser_runtime.workflow_replay_executor_design import FORBIDDEN_EFFECTS


WORKFLOW_REPLAY_EXECUTION_PROOF_VERSION = "browser.workflow_replay_execution_proof.v1"
WORKFLOW_REPLAY_EXECUTION_PROOF_COMPLETE = "workflow_replay_execution_proof_complete"
WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED = "blocked_workflow_replay_execution_proof"
WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED_NO_EXECUTION_REQUESTED = (
    "blocked_workflow_replay_execution_proof_no_execution_requested"
)
WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED_MARKER_EXISTS = (
    "blocked_workflow_replay_execution_proof_idempotency_marker_exists"
)
WORKFLOW_REPLAY_EXECUTION_PROOF_FAILED = "failed_workflow_replay_execution_proof"
WORKFLOW_REPLAY_EXECUTION_PROOF_RECORD_TYPE = "browser_workflow_replay_execution_proof"

LOCAL_ONLY_DOMAINS = {"127.0.0.1", "localhost", "::1"}
ALLOWED_HARMLESS_TARGETS = {
    "Approvals tab": "[data-testid='tab-approvals']",
    "Workflow tab": "[data-testid='tab-workflow']",
    "Mark panel inspected button": "[data-testid='harmless-inspect-action']",
}
BLOCKED_EFFECTS = (
    *FORBIDDEN_EFFECTS,
    "real_profile_access_attempted",
    "credential_or_cookie_read_attempted",
    "cookie_export_attempted",
    "browser_history_import_attempted",
    "public_tunnel_attempted",
    "trusted_skill_write_attempted",
    "skill_activation_attempted",
    "canonical_writeback_attempted",
    "agent_bus_enqueue_attempted",
    "provider_call_attempted",
    "gate_mutation_attempted",
    "shell_execution_from_browser_runtime_attempted",
)


class WorkflowReplayBrowserController(Protocol):
    """Controller surface required by the safe-local replay proof."""

    def ensure_available(self) -> dict[str, Any]:
        """Return readiness information or raise to block before marker write."""

    def open(self, url: str) -> dict[str, Any]:
        """Open the target URL."""

    def read_state(self) -> dict[str, Any]:
        """Read visible/browser state."""

    def harmless_click(self, target: str) -> dict[str, Any]:
        """Perform one allowlisted harmless UI click."""

    def capture_screenshot(self) -> bytes:
        """Capture a screenshot as bytes."""

    def close(self) -> None:
        """Close the browser/session."""


class LiveCDPWorkflowReplayController:
    """Minimal live controller for the local VincisOS replay proof.

    The controller is intentionally narrow: it supports only the known
    local-product test target harmless actions by stable `data-testid`
    selectors. It does not expose free-form JavaScript to callers.
    """

    def __init__(self) -> None:
        from runtime.browser_runtime.cdp_live import IsolatedBrowserLauncher, MinimalCDPClient

        self.launcher = IsolatedBrowserLauncher()
        self.client = MinimalCDPClient()
        self.connected = False

    def ensure_available(self) -> dict[str, Any]:
        return dict(self.launcher.ensure_available())

    def open(self, url: str) -> dict[str, Any]:
        launch = dict(self.launcher.launch() or {})
        endpoint = str(launch.get("cdp_endpoint") or "")
        self.client.connect(endpoint)
        self.connected = True
        self.client.navigate(url)
        return {"opened_url": url, "profile_policy": "throwaway_only", "launch": launch}

    def read_state(self) -> dict[str, Any]:
        return dict(self.client.read_state() or {})

    def harmless_click(self, target: str) -> dict[str, Any]:
        selector = ALLOWED_HARMLESS_TARGETS.get(target)
        if not selector:
            raise RuntimeError(f"harmless click target is not allowlisted: {target}")
        expression = (
            "(() => {"
            f"const el = document.querySelector({json.dumps(selector)});"
            "if (!el) return {ok:false, reason:'selector_not_found'};"
            "el.click();"
            "return {ok:true, selector:"
            f"{json.dumps(selector)}"
            ", text:(el.textContent || '').trim(), url:location.href};"
            "})()"
        )
        result = self.client._eval(expression)  # noqa: SLF001 - bounded wrapper over local controller.
        if not isinstance(result, dict) or not result.get("ok"):
            raise RuntimeError(f"harmless click failed for {target}: {result}")
        return result

    def capture_screenshot(self) -> bytes:
        return bytes(self.client.capture_screenshot() or b"")

    def close(self) -> None:
        try:
            self.client.close()
        finally:
            self.launcher.close()


@dataclass(frozen=True)
class WorkflowReplayExecutionProofRequest:
    """Request for one bounded local workflow replay proof."""

    workflow_id: str = ""
    target_url: str = ""
    allowed_domains: list[str] = field(default_factory=list)
    requested_by: str = "Codex"
    operator_id: str = "operator"
    execute_local_replay: bool = False
    run_slug: str = ""
    retry_after_failed_marker: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowReplayProofAction:
    """One workflow action outcome."""

    step_id: str
    action_type: str
    target: str
    status: str
    notes: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowReplayExecutionProofResult:
    """Result for a bounded workflow replay execution proof."""

    record_type: str
    version: str
    generated_at: str
    status: str
    run_id: str
    workflow_id: str
    workflow_entry_path: str
    target_url: str
    target_domain: str
    approval_request_id: str
    approval_request_path: str
    idempotency_marker_path: str
    request: WorkflowReplayExecutionProofRequest
    actions: list[WorkflowReplayProofAction] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    approval_request_written: bool = False
    idempotency_marker_written: bool = False
    workflow_replay_attempted: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    screenshot_attempted: bool = False
    browser_run_log_written: bool = False
    agent_activity_log_written: bool = False
    screenshot_artifact_written: bool = False
    draft_skill_written: bool = False
    untrusted_candidate_written: bool = False
    approval_request_record_path: str = ""
    browser_run_log_path: str = ""
    agent_activity_log_path: str = ""
    screenshot_path: str = ""
    draft_skill_path: str = ""
    skill_candidate_path: str = ""
    error: str = ""
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    external_code_copied: bool = False
    workflow_use_reference_only: bool = True
    browser_harness_reference_only: bool = True
    denied_effects: dict[str, bool] = field(default_factory=dict)
    next_step: str = "review_browser_replay_proof"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        payload["actions"] = [action.as_dict() for action in self.actions]
        return payload

    def validate(self) -> None:
        if self.real_profile_access_attempted:
            raise ValueError("real_profile_access_attempted must remain false")
        if self.credential_or_cookie_read_attempted:
            raise ValueError("credential_or_cookie_read_attempted must remain false")
        if self.trusted_skill_write_attempted:
            raise ValueError("trusted_skill_write_attempted must remain false")
        if self.skill_activation_attempted:
            raise ValueError("skill_activation_attempted must remain false")
        if self.canonical_writeback_attempted:
            raise ValueError("canonical_writeback_attempted must remain false")
        if self.agent_bus_enqueue_attempted:
            raise ValueError("agent_bus_enqueue_attempted must remain false")
        if self.provider_call_attempted:
            raise ValueError("provider_call_attempted must remain false")
        if self.gate_mutation_attempted:
            raise ValueError("gate_mutation_attempted must remain false")
        if self.external_code_copied:
            raise ValueError("external_code_copied must remain false")
        if not self.workflow_use_reference_only:
            raise ValueError("workflow_use_reference_only must remain true")
        if not self.browser_harness_reference_only:
            raise ValueError("browser_harness_reference_only must remain true")
        for effect in BLOCKED_EFFECTS:
            if self.denied_effects.get(effect) is not False:
                raise ValueError(f"{effect} must remain false")
        if self.status == WORKFLOW_REPLAY_EXECUTION_PROOF_COMPLETE:
            if self.blockers:
                raise ValueError("complete proof cannot include blockers")
            if not self.approval_request_written:
                raise ValueError("complete proof requires approval request write")
            if not self.idempotency_marker_written:
                raise ValueError("complete proof requires idempotency marker write")
            if not self.workflow_replay_attempted:
                raise ValueError("complete proof requires workflow replay attempt")
            if not self.browser_run_log_written or not self.agent_activity_log_written:
                raise ValueError("complete proof requires run and activity logs")
            if not self.draft_skill_written or not self.untrusted_candidate_written:
                raise ValueError("complete proof requires draft-only skill evidence")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _date_slug(timestamp: str) -> str:
    return timestamp[:10]


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _load_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_write_json_create_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _run_id(request: WorkflowReplayExecutionProofRequest, timestamp: str) -> str:
    if request.run_slug:
        return slugify(request.run_slug, "workflow-replay-execution-proof")
    stamp = timestamp[:10].replace("-", "")
    workflow = slugify(request.workflow_id, "workflow")
    return f"workflow_replay_execution_proof_{stamp}_{workflow}"


def _approval_record(
    *,
    generated_at: str,
    approval: Any,
    request: WorkflowReplayExecutionProofRequest,
) -> dict[str, Any]:
    return {
        "record_type": "browser_workflow_replay_execution_approval_request",
        "schema_version": WORKFLOW_REPLAY_EXECUTION_PROOF_VERSION,
        "approval_request_id": approval.approval_request_id,
        "status": "approved_for_single_local_trial",
        "operation": "browser_workflow_replay_execution_trial",
        "requested_by": request.requested_by,
        "operator_id": request.operator_id,
        "approved_by": request.operator_id,
        "approved_at": generated_at,
        "workflow_id": approval.workflow_id,
        "workflow_entry_path": approval.workflow_entry_path,
        "target_url": approval.target_url,
        "target_domain": approval.target_domain,
        "allowed_domains": list(approval.allowed_domains),
        "request_digest_sha256": approval.request_digest_sha256,
        "browser_profile_policy": "throwaway_only",
        "allow_real_profile": False,
        "allow_credentials": False,
        "allow_cookie_export": False,
        "activation_allowed": False,
        "trusted_write_allowed": False,
        "skill_activation_allowed": False,
        "canonical_writeback_allowed": False,
        "approval_scope": "one local VincisOS workflow replay proof only",
    }


def _marker_record(
    *,
    generated_at: str,
    run_id: str,
    approval: Any,
    request: WorkflowReplayExecutionProofRequest,
) -> dict[str, Any]:
    return {
        "record_type": "browser_workflow_replay_execution_idempotency_marker",
        "schema_version": WORKFLOW_REPLAY_EXECUTION_PROOF_VERSION,
        "approval_request_id": approval.approval_request_id,
        "workflow_id": approval.workflow_id,
        "target_url": approval.target_url,
        "request_digest_sha256": approval.request_digest_sha256,
        "reserved_at": generated_at,
        "reserved_by": request.requested_by,
        "run_id": run_id,
        "status": "reserved_before_browser_launch",
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "workflow_replay_attempted": False,
        "completed_at": None,
        "failed_at": None,
    }


def _retry_suffix(run_id: str) -> str:
    return hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:12]


def _failed_marker_retry_allowed(marker_path_text: str) -> tuple[bool, str]:
    marker_path = Path(marker_path_text)
    if not marker_path.exists():
        return False, "failed_marker_not_found"
    try:
        marker = _load_json(marker_path)
    except Exception:
        return False, "failed_marker_unreadable"
    if marker.get("status") != "failed":
        return False, "existing_marker_not_failed"
    run_log_path = marker.get("browser_run_log_path")
    if not isinstance(run_log_path, str) or not run_log_path:
        return False, "failed_marker_missing_run_log"
    run_log = Path(run_log_path)
    if not run_log.exists():
        return False, "failed_marker_run_log_not_found"
    try:
        payload = _load_json(run_log)
    except Exception:
        return False, "failed_marker_run_log_unreadable"
    if payload.get("status") != WORKFLOW_REPLAY_EXECUTION_PROOF_FAILED:
        return False, "failed_marker_run_log_not_failed"
    forbidden_true = [
        flag
        for flag in (
            "allow_real_profile",
            "allow_credentials",
            "trusted_skill_write_allowed",
            "skill_activation_allowed",
            "canonical_writeback_allowed",
        )
        if payload.get(flag, False) is not False
    ]
    if forbidden_true:
        return False, "failed_marker_forbidden_flags_not_false"
    return True, ""


def _artifact_paths(vault: Path, *, run_id: str, target_domain: str, date_slug: str) -> dict[str, Path]:
    domain_slug = slugify(target_domain, "local")
    return {
        "browser_run": vault / "07_LOGS" / "Browser-Runs" / f"{run_id}_success.json",
        "browser_run_failed": vault / "07_LOGS" / "Browser-Runs" / f"{run_id}_failed.json",
        "screenshot": vault / "07_LOGS" / "Browser-Runs" / f"{run_id}_screenshot.png",
        "agent_activity": vault / "07_LOGS" / "Agent-Activity" / f"{date_slug}-browser-workflow-replay-execution-proof.md",
        "draft_skill": vault / "06_AGENTS" / "Browser-Skills" / "_drafts" / f"draft-{run_id}.md",
        "candidate": vault
        / "03_INPUTS"
        / "Browser-Skill-Candidates"
        / domain_slug
        / f"{date_slug.replace('-', '')}__candidate-{run_id}.md",
    }


def _draft_skill_content(
    *,
    run_id: str,
    target_domain: str,
    workflow_id: str,
    browser_run_path: Path,
    screenshot_path: Path,
    actions: list[WorkflowReplayProofAction],
) -> str:
    action_lines = "\n".join(f"- {item.action_type}: {item.target} -> {item.status}" for item in actions)
    return f"""---
type: browser-skill-draft
status: draft
activation_allowed: false
review_required: true
source_run_id: {run_id}
domain: {target_domain}
---

# Draft Browser Skill - {target_domain} Workflow Replay

This draft records reusable local-site knowledge from a bounded ChaseOS workflow
replay proof. It is not active runtime memory and must be reviewed before any
promotion.

## Source Evidence

- Workflow: `{workflow_id}`
- Browser run log: `{browser_run_path.as_posix()}`
- Screenshot: `{screenshot_path.as_posix()}`

## Durable Patterns

- Open only the reviewed local target URL.
- Use stable `data-testid` selectors for the product UI test target.
- Verify the harmless action status after clicking `Mark panel inspected`.
- Keep this draft free of secrets, cookies, session state, real profile paths,
  and browser history.

## Replay Actions

{action_lines}

## Forbidden

- No trusted skill activation.
- No credential or cookie reads.
- No real browser profile use.
- No canonical ChaseOS writeback.
"""


def _candidate_content(
    *,
    run_id: str,
    target_domain: str,
    workflow_id: str,
    browser_run_path: Path,
    draft_skill_path: Path,
) -> str:
    return f"""---
type: browser-skill-candidate
status: untrusted-candidate
approval_status: pending-review
activation_allowed: false
source_run_id: {run_id}
domain: {target_domain}
---

# Browser Skill Candidate - {target_domain} Workflow Replay

Untrusted candidate generated from a ChaseOS-controlled local workflow replay
proof.

- Workflow: `{workflow_id}`
- Browser run log: `{browser_run_path.as_posix()}`
- Draft skill: `{draft_skill_path.as_posix()}`
- Promotion: blocked until explicit review.
- Secrets/cookies/session/profile data: not stored.
"""


def _activity_content(
    *,
    run_id: str,
    status: str,
    workflow_id: str,
    target_url: str,
    browser_run_path: Path,
    screenshot_path: Path,
    draft_skill_path: Path,
    candidate_path: Path,
) -> str:
    return f"""---
runtime: Codex
activity_type: browser-workflow-replay-execution-proof
status: {status}
run_id: {run_id}
---

# Browser Workflow Replay Execution Proof

- Workflow: `{workflow_id}`
- Target URL: `{target_url}`
- Browser run log: `{browser_run_path.as_posix()}`
- Screenshot: `{screenshot_path.as_posix()}`
- Draft skill: `{draft_skill_path.as_posix()}`
- Skill candidate: `{candidate_path.as_posix()}`
- Real profile, credentials, cookies, session tokens, browser history: not used.
- Trusted skill activation, Gate mutation, Agent Bus enqueue, provider calls, canonical writeback: not performed.
"""


def _execute_steps(
    *,
    controller: WorkflowReplayBrowserController,
    entry: dict[str, Any],
    target_url: str,
) -> tuple[list[WorkflowReplayProofAction], bytes, dict[str, Any]]:
    actions: list[WorkflowReplayProofAction] = []
    screenshot = b""
    final_state: dict[str, Any] = {}
    opened = False
    for index, step in enumerate(entry.get("steps") or []):
        if not isinstance(step, dict):
            continue
        step_id = str(step.get("step_id") or f"step_{index + 1:02d}")
        action_type = str(step.get("action_type") or "")
        target = str(step.get("target") or "")
        if action_type == "open":
            evidence = controller.open(target_url)
            opened = True
        elif action_type == "read_state":
            if not opened:
                evidence = controller.open(target_url)
                opened = True
            evidence = controller.read_state()
            final_state = dict(evidence)
        elif action_type == "harmless_click":
            evidence = controller.harmless_click(target)
            final_state = controller.read_state()
        elif action_type == "capture_screenshot":
            screenshot = controller.capture_screenshot()
            evidence = {"screenshot_bytes": len(screenshot)}
        else:
            raise RuntimeError(f"unsupported workflow replay action type: {action_type}")
        actions.append(
            WorkflowReplayProofAction(
                step_id=step_id,
                action_type=action_type,
                target=target,
                status="succeeded",
                notes=str(step.get("notes") or ""),
                evidence=evidence if isinstance(evidence, dict) else {"result": str(evidence)},
            )
        )
    if not screenshot:
        screenshot = controller.capture_screenshot()
    return actions, screenshot, final_state


def run_workflow_replay_execution_proof(
    vault_root: str | Path,
    request: WorkflowReplayExecutionProofRequest,
    *,
    generated_at: str | None = None,
    controller: WorkflowReplayBrowserController | None = None,
) -> WorkflowReplayExecutionProofResult:
    """Run one approval-gated local workflow replay proof."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    approval_request = WorkflowReplayExecutionApprovalRequest(
        workflow_id=request.workflow_id,
        target_url=request.target_url,
        allowed_domains=list(request.allowed_domains),
        requested_by=request.requested_by,
        operator_id=request.operator_id,
    )
    approval = build_workflow_replay_execution_approval(vault, approval_request, generated_at=timestamp)
    run_id = _run_id(request, timestamp)
    target_domain = approval.target_domain or domain_from_url(request.target_url)
    blockers: list[str] = []
    failed_marker_retry = False
    if approval.idempotency_marker_exists and request.retry_after_failed_marker:
        failed_marker_retry, retry_blocker = _failed_marker_retry_allowed(approval.idempotency_marker_path)
        if retry_blocker:
            blockers.append(retry_blocker)
    if approval.status != WORKFLOW_REPLAY_EXECUTION_APPROVAL_READY:
        approval_blockers = list(approval.blockers)
        if failed_marker_retry:
            approval_blockers = [item for item in approval_blockers if item != "idempotency_marker_absent"]
        if approval_blockers or not failed_marker_retry:
            blockers.extend(["approval_contract_not_ready", *approval_blockers])
    if target_domain not in LOCAL_ONLY_DOMAINS:
        blockers.append("target_domain_not_local_only")
    if not request.execute_local_replay:
        blockers.append("execute_local_replay_false")
    if approval.idempotency_marker_exists and not request.retry_after_failed_marker:
        blockers.append("idempotency_marker_exists")
    if blockers:
        status = (
            WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED_NO_EXECUTION_REQUESTED
            if blockers == ["execute_local_replay_false"]
            else (
                WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED_MARKER_EXISTS
                if "idempotency_marker_exists" in blockers
                else WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED
            )
        )
        result = WorkflowReplayExecutionProofResult(
            record_type=WORKFLOW_REPLAY_EXECUTION_PROOF_RECORD_TYPE,
            version=WORKFLOW_REPLAY_EXECUTION_PROOF_VERSION,
            generated_at=timestamp,
            status=status,
            run_id=run_id,
            workflow_id=approval.workflow_id,
            workflow_entry_path=approval.workflow_entry_path,
            target_url=approval.target_url,
            target_domain=target_domain,
            approval_request_id=approval.approval_request_id,
            approval_request_path=approval.approval_request_path,
            idempotency_marker_path=approval.idempotency_marker_path,
            request=request,
            blockers=blockers,
            denied_effects={effect: False for effect in BLOCKED_EFFECTS},
            next_step="repair_or_approve_workflow_replay_execution_proof",
        )
        result.validate()
        return result

    live_controller = controller or LiveCDPWorkflowReplayController()
    try:
        live_controller.ensure_available()
    except Exception as exc:
        result = WorkflowReplayExecutionProofResult(
            record_type=WORKFLOW_REPLAY_EXECUTION_PROOF_RECORD_TYPE,
            version=WORKFLOW_REPLAY_EXECUTION_PROOF_VERSION,
            generated_at=timestamp,
            status=WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED,
            run_id=run_id,
            workflow_id=approval.workflow_id,
            workflow_entry_path=approval.workflow_entry_path,
            target_url=approval.target_url,
            target_domain=target_domain,
            approval_request_id=approval.approval_request_id,
            approval_request_path=approval.approval_request_path,
            idempotency_marker_path=approval.idempotency_marker_path,
            request=request,
            blockers=["browser_controller_unavailable"],
            error=str(exc),
            denied_effects={effect: False for effect in BLOCKED_EFFECTS},
            next_step="configure_local_throwaway_browser_or_injected_test_controller",
        )
        result.validate()
        return result

    approval_path = Path(approval.approval_request_path)
    marker_path = Path(approval.idempotency_marker_path)
    approval_request_id = approval.approval_request_id
    if failed_marker_retry:
        retry_suffix = _retry_suffix(run_id)
        approval_request_id = f"{approval.approval_request_id}-retry-{retry_suffix}"
        approval_path = approval_path.with_name(f"browser-workflow-replay-retry-{retry_suffix}{approval_path.suffix}")
        marker_path = marker_path.with_name(f"browser-workflow-replay-retry-{retry_suffix}{marker_path.suffix}")
    if approval_path.exists() or marker_path.exists():
        result = WorkflowReplayExecutionProofResult(
            record_type=WORKFLOW_REPLAY_EXECUTION_PROOF_RECORD_TYPE,
            version=WORKFLOW_REPLAY_EXECUTION_PROOF_VERSION,
            generated_at=timestamp,
            status=WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED_MARKER_EXISTS,
            run_id=run_id,
            workflow_id=approval.workflow_id,
            workflow_entry_path=approval.workflow_entry_path,
            target_url=approval.target_url,
            target_domain=target_domain,
            approval_request_id=approval_request_id,
            approval_request_path=approval_path.as_posix(),
            idempotency_marker_path=marker_path.as_posix(),
            request=request,
            blockers=["approval_or_marker_already_exists"],
            denied_effects={effect: False for effect in BLOCKED_EFFECTS},
            next_step="review_existing_approval_or_marker_before_retry",
        )
        result.validate()
        return result

    entry = _load_json(approval.workflow_entry_path)
    date_slug = _date_slug(timestamp)
    paths = _artifact_paths(vault, run_id=run_id, target_domain=target_domain, date_slug=date_slug)
    approval_record = _approval_record(generated_at=timestamp, approval=approval, request=request)
    approval_record["approval_request_id"] = approval_request_id
    approval_record["approval_request_path"] = approval_path.as_posix()
    approval_record["retry_after_failed_marker"] = failed_marker_retry
    marker_record = _marker_record(generated_at=timestamp, run_id=run_id, approval=approval, request=request)
    marker_record["approval_request_id"] = approval_request_id
    marker_record["retry_after_failed_marker"] = failed_marker_retry
    _safe_write_json_create_new(approval_path, approval_record)
    _safe_write_json_create_new(marker_path, marker_record)

    actions: list[WorkflowReplayProofAction] = []
    screenshot = b""
    final_state: dict[str, Any] = {}
    failed_error = ""
    try:
        actions, screenshot, final_state = _execute_steps(
            controller=live_controller,
            entry=entry,
            target_url=approval.target_url,
        )
    except Exception as exc:
        failed_error = str(exc)
    finally:
        try:
            live_controller.close()
        except Exception:
            pass

    completed = not failed_error
    run_path = paths["browser_run"] if completed else paths["browser_run_failed"]
    if completed:
        _write_bytes(paths["screenshot"], screenshot)
    run_payload = {
        "record_type": WORKFLOW_REPLAY_EXECUTION_PROOF_RECORD_TYPE,
        "schema_version": WORKFLOW_REPLAY_EXECUTION_PROOF_VERSION,
        "status": WORKFLOW_REPLAY_EXECUTION_PROOF_COMPLETE if completed else WORKFLOW_REPLAY_EXECUTION_PROOF_FAILED,
        "run_id": run_id,
        "workflow_id": approval.workflow_id,
        "target_url": approval.target_url,
        "target_domain": target_domain,
        "approval_request_id": approval_request_id,
        "approval_request_path": approval_path.as_posix(),
        "idempotency_marker_path": marker_path.as_posix(),
        "actions": [action.as_dict() for action in actions],
        "final_state": final_state,
        "error": failed_error,
        "browser_profile_policy": "throwaway_only",
        "allow_real_profile": False,
        "allow_credentials": False,
        "trusted_skill_write_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
        "external_code_copied": False,
        "workflow_use_reference_only": True,
        "browser_harness_reference_only": True,
    }
    _safe_write_json_create_new(run_path, run_payload)
    marker_after = _load_json(marker_path)
    marker_after.update(
        {
            "status": "completed" if completed else "failed",
            "completed_at": timestamp if completed else None,
            "failed_at": timestamp if not completed else None,
            "browser_launch_attempted": True,
            "cdp_connection_attempted": True,
            "workflow_replay_attempted": True,
            "browser_run_log_path": run_path.as_posix(),
        }
    )
    marker_path.write_text(json.dumps(marker_after, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if completed:
        _write_text(
            paths["draft_skill"],
            _draft_skill_content(
                run_id=run_id,
                target_domain=target_domain,
                workflow_id=approval.workflow_id,
                browser_run_path=run_path,
                screenshot_path=paths["screenshot"],
                actions=actions,
            ),
        )
        _write_text(
            paths["candidate"],
            _candidate_content(
                run_id=run_id,
                target_domain=target_domain,
                workflow_id=approval.workflow_id,
                browser_run_path=run_path,
                draft_skill_path=paths["draft_skill"],
            ),
        )
        _write_text(
            paths["agent_activity"],
            _activity_content(
                run_id=run_id,
                status=WORKFLOW_REPLAY_EXECUTION_PROOF_COMPLETE,
                workflow_id=approval.workflow_id,
                target_url=approval.target_url,
                browser_run_path=run_path,
                screenshot_path=paths["screenshot"],
                draft_skill_path=paths["draft_skill"],
                candidate_path=paths["candidate"],
            ),
        )

    result = WorkflowReplayExecutionProofResult(
        record_type=WORKFLOW_REPLAY_EXECUTION_PROOF_RECORD_TYPE,
        version=WORKFLOW_REPLAY_EXECUTION_PROOF_VERSION,
        generated_at=timestamp,
        status=WORKFLOW_REPLAY_EXECUTION_PROOF_COMPLETE if completed else WORKFLOW_REPLAY_EXECUTION_PROOF_FAILED,
        run_id=run_id,
        workflow_id=approval.workflow_id,
        workflow_entry_path=approval.workflow_entry_path,
        target_url=approval.target_url,
        target_domain=target_domain,
        approval_request_id=approval_request_id,
        approval_request_path=approval_path.as_posix(),
        idempotency_marker_path=marker_path.as_posix(),
        request=request,
        actions=actions,
        blockers=[] if completed else ["workflow_replay_execution_failed"],
        approval_request_written=True,
        idempotency_marker_written=True,
        workflow_replay_attempted=True,
        browser_launch_attempted=True,
        cdp_connection_attempted=True,
        screenshot_attempted=completed,
        browser_run_log_written=True,
        agent_activity_log_written=completed,
        screenshot_artifact_written=completed,
        draft_skill_written=completed,
        untrusted_candidate_written=completed,
        approval_request_record_path=approval_path.as_posix(),
        browser_run_log_path=run_path.as_posix(),
        agent_activity_log_path=paths["agent_activity"].as_posix() if completed else "",
        screenshot_path=paths["screenshot"].as_posix() if completed else "",
        draft_skill_path=paths["draft_skill"].as_posix() if completed else "",
        skill_candidate_path=paths["candidate"].as_posix() if completed else "",
        error=failed_error,
        denied_effects={effect: False for effect in BLOCKED_EFFECTS},
        next_step="review_browser_replay_skill_candidate" if completed else "inspect_failed_replay_artifact",
    )
    result.validate()
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one bounded local Browser Workflow replay proof.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--workflow-id", required=True, help="Reviewed workflow id to execute.")
    parser.add_argument("--target-url", required=True, help="Local target URL.")
    parser.add_argument("--allowed-domain", action="append", default=[], help="Allowed local domain. May be repeated.")
    parser.add_argument("--requested-by", default="Codex")
    parser.add_argument("--operator-id", default="operator")
    parser.add_argument("--execute-local-replay", action="store_true", help="Actually run the bounded local replay.")
    parser.add_argument(
        "--retry-after-failed-marker",
        action="store_true",
        help="Permit a retry marker only when the existing marker is failed and its failed run log is safe.",
    )
    parser.add_argument("--run-slug", default="")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = run_workflow_replay_execution_proof(
        args.vault_root,
        WorkflowReplayExecutionProofRequest(
            workflow_id=args.workflow_id,
            target_url=args.target_url,
            allowed_domains=list(args.allowed_domain or []),
            requested_by=args.requested_by,
            operator_id=args.operator_id,
            execute_local_replay=args.execute_local_replay,
            run_slug=args.run_slug,
            retry_after_failed_marker=args.retry_after_failed_marker,
        ),
    )
    payload = result.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {result.status}")
        print(f"run_id: {result.run_id}")
        print(f"browser_run_log_path: {result.browser_run_log_path}")
        print(f"next_step: {result.next_step}")
    return 0 if result.status == WORKFLOW_REPLAY_EXECUTION_PROOF_COMPLETE else 2


if __name__ == "__main__":
    raise SystemExit(main())
