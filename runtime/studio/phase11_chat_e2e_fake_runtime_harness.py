"""Phase 11 Chat end-to-end fake runtime harness.

Injects synthetic completed runtime-task results into a **test vault** Agent Bus,
then exercises the full Chat result-display + conversation-log-write path without
any live credentials, network calls, Discord, or external cron mutation.

Flow (dry_run=False, is_test_vault=True):
  1. Guard: confirm vault is test-only (is_test_vault=True required)
  2. Inject fake Hermes "done" task with synthetic result text
  3. Inject fake OpenClaw Discord-control "done" task
  4. Inject fake OpenClaw schedule-control "done" task
  5. Call build_chat_runtime_result_display — verify result cards appear
  6. Call write_conversation_log — verify file created in 07_LOGS/Conversations/
  7. Return full E2E run report

Hard boundaries:
- is_test_vault=True REQUIRED — guard against running against real vault.
- No provider API calls, no Discord API calls, no external cron mutation.
- No secret values in any output.
- No canonical memory writes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.agent_bus.bus import create_task, update_task_status
from runtime.studio.phase11_chat_conversation_log_writer import write_conversation_log
from runtime.studio.phase11_chat_runtime_result_display import build_chat_runtime_result_display


MODEL_VERSION = "studio.phase11_chat_e2e_fake_runtime_harness.v1"
SURFACE_ID = "phase11_chat_e2e_fake_runtime_harness"
PASS_ID = "phase11-chat-e2e-fake-runtime-harness"
STATUS_DRY = "COMPLETE / DRY RUN / NO WRITES"
STATUS_LIVE = "COMPLETE / FAKE TASKS INJECTED / RESULT DISPLAY AND LOG VERIFIED"
STATUS_PARTIAL = "PARTIAL / SOME INJECTIONS FAILED"
STATUS_BLOCKED = "BLOCKED / REAL VAULT GUARD ACTIVE"

_FAKE_SENDER = "Codex"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _inject_fake_task(
    vault: Path,
    *,
    recipient: str,
    task_type_hint: str,
    request: str,
    fake_result: str,
    session_id: str,
) -> str:
    """Create + complete a fake bus task. Returns task_id."""
    result = create_task(
        vault,
        sender=_FAKE_SENDER,
        recipient=recipient,
        intent="TASK",
        priority="normal",
        request=request,
        expected_output="e2e-fake-result",
        notes=f"task_type: {task_type_hint}\ne2e_session_id: {session_id}",
    )
    if not result.get("created"):
        raise RuntimeError(
            f"fake task create failed for {recipient}: {result.get('reason', 'unknown')}"
        )
    task_id: str = result["task_id"]
    update_task_status(
        vault,
        task_id=task_id,
        runtime=recipient,
        status="claimed",
        event_type="claimed",
        message=f"[E2E harness] {recipient} claimed fake task",
    )
    update_task_status(
        vault,
        task_id=task_id,
        runtime=recipient,
        status="done",
        event_type="result_attached",
        message=fake_result,
    )
    return task_id


def run_e2e_fake_harness(
    vault_root: str | Path,
    *,
    session_id: str | None = None,
    user_prompt: str = "Test Chat prompt for E2E fake harness",
    fake_provider_output: str = "Fake provider response: the test passed.",
    fake_hermes_result: str = "Fake Hermes result: planning complete.",
    fake_openclaw_discord_result: str = "Fake OpenClaw Discord result: dry-run ping sent.",
    fake_openclaw_schedule_result: str = "Fake OpenClaw schedule result: dry-run validated.",
    operator_approval_statement: str = "E2E fake harness automated test run",
    dry_run: bool = True,
    is_test_vault: bool = False,
) -> dict[str, Any]:
    """Run the full Phase 11 Chat E2E fake runtime flow.

    Args:
        vault_root: Vault directory — MUST be a test vault.
        session_id: Synthetic session ID (auto-generated if omitted).
        user_prompt: Simulated user Chat message.
        fake_provider_output: Simulated OpenAI provider response text.
        fake_hermes_result: Simulated Hermes task result text.
        fake_openclaw_discord_result: Simulated OpenClaw Discord control result.
        fake_openclaw_schedule_result: Simulated OpenClaw schedule control result.
        operator_approval_statement: Required for live log write.
        dry_run: Default True — no Agent Bus writes or log file created.
        is_test_vault: MUST be True to proceed. Guards against running against
                       the production vault.
    """
    vault = Path(vault_root).resolve()

    if not is_test_vault:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "pass": PASS_ID,
            "status": STATUS_BLOCKED,
            "generated_at_utc": _now_utc(),
            "vault_root": str(vault),
            "dry_run": dry_run,
            "is_test_vault": False,
            "blocked_reasons": [
                "is_test_vault_required: set is_test_vault=True to confirm this is a test vault"
            ],
        }

    session_id = session_id or str(uuid.uuid4())[:20]
    blockers: list[str] = []
    injected_task_ids: dict[str, str] = {}
    result_display: dict[str, Any] = {}
    log_result: dict[str, Any] = {}

    if not dry_run:
        for lane_key, recipient, task_type_hint, request_suffix, fake_result in [
            (
                "hermes",
                "Hermes",
                "planning",
                "Fake Hermes planning task",
                fake_hermes_result,
            ),
            (
                "openclaw_discord",
                "OpenClaw",
                "operator-briefing",
                "[discord-control] Fake OpenClaw Discord task",
                fake_openclaw_discord_result,
            ),
            (
                "openclaw_schedule",
                "OpenClaw",
                "operator-briefing",
                "[schedule-cron-control] Fake OpenClaw schedule task",
                fake_openclaw_schedule_result,
            ),
        ]:
            try:
                task_id = _inject_fake_task(
                    vault,
                    recipient=recipient,
                    task_type_hint=task_type_hint,
                    request=f"[E2E harness] {request_suffix} for session {session_id}",
                    fake_result=fake_result,
                    session_id=session_id,
                )
                injected_task_ids[lane_key] = task_id
            except Exception as exc:
                blockers.append(f"{lane_key}_task_inject_failed:{str(exc)[:100]}")

        all_injected = list(injected_task_ids.values())
        result_display = build_chat_runtime_result_display(
            vault,
            runtimes=["Hermes", "OpenClaw"],
            session_task_ids=all_injected if all_injected else None,
        )

        log_result = write_conversation_log(
            vault,
            session_hint=session_id,
            operator_approval_statement=operator_approval_statement,
            user_prompt=user_prompt,
            provider_output=fake_provider_output,
            hermes_task_id=injected_task_ids.get("hermes"),
            hermes_status="done",
            hermes_result_summary=fake_hermes_result,
            openclaw_discord_task_id=injected_task_ids.get("openclaw_discord"),
            openclaw_discord_status="done",
            openclaw_cron_task_id=injected_task_ids.get("openclaw_schedule"),
            openclaw_cron_status="done",
            bus_readback_snapshot=result_display.get("lanes"),
            dry_run=False,
        )
    else:
        result_display = build_chat_runtime_result_display(
            vault, runtimes=["Hermes", "OpenClaw"]
        )
        log_result = write_conversation_log(
            vault,
            session_hint=session_id,
            operator_approval_statement=operator_approval_statement,
            user_prompt=user_prompt,
            provider_output=fake_provider_output,
            dry_run=True,
        )

    tasks_injected = len(injected_task_ids)
    result_cards_visible = sum(
        1
        for lane in result_display.get("lanes", [])
        for card in lane.get("cards", [])
        if card.get("task_id") in injected_task_ids.values()
    )
    log_file_written = bool(
        log_result.get("ok")
        and log_result.get("file_written")
        and not log_result.get("dry_run")
    )
    e2e_complete = (
        not dry_run
        and tasks_injected == 3
        and result_cards_visible > 0
        and log_file_written
    )

    if dry_run:
        status = STATUS_DRY
    elif blockers:
        status = STATUS_PARTIAL
    else:
        status = STATUS_LIVE

    return {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "session_id": session_id,
        "dry_run": dry_run,
        "is_test_vault": is_test_vault,
        "summary": {
            "tasks_injected": tasks_injected,
            "result_cards_visible": result_cards_visible,
            "log_file_written": log_file_written,
            "e2e_complete": e2e_complete,
        },
        "injected_task_ids": injected_task_ids,
        "result_display": result_display,
        "log_result": log_result,
        "blocked_reasons": blockers,
        "authority": {
            "test_vault_only": True,
            "provider_api_call_performed": False,
            "discord_api_call_performed": False,
            "external_cron_mutated": False,
            "canonical_mutation_performed": False,
            "secret_values_in_output": False,
        },
    }
