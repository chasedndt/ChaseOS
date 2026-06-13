"""
hermes_review_execute.py — Hermes Review Execution (Phase 9 Agent Bus)

Hermes-side workflow for claiming and executing a review task from the coordination bus.

Lifecycle:
  1. Find the task (by task_id input, or claim oldest open review task for Hermes)
  2. Claim the task (bus: claimed)
  3. Mark in_progress (bus: in_progress)
  4. Read the artifact at artifact_path if within review scope
  5. Produce a structural review + optional LLM synthesis
  6. Post result back to bus (bus: done) with review summary in message
  7. Write agent-activity audit entry

Review scope (artifacts Hermes may read):
  07_LOGS/Operator-Briefs/, 07_LOGS/SBP-Runs/, 07_LOGS/Build-Logs/, runtime/agent_bus/

Artifacts outside review scope: escalate — do not read, post escalation to bus.

LLM synthesis:
  _execute_synthesis() routes through the shared runtime execution adapter using
  the Hermes model_config.yaml chain to produce a prose interpretation of the structural findings.
  Synthesis is fail-open — if the API call fails for any reason, the structural review
  stands alone and no error is raised.

Inputs:
  - task_id         str   (optional) specific task to claim; if omitted, claims oldest open
  - synthesize      bool  (optional, default False) set True to enable LLM synthesis (opt-in only)

Outputs (in returned dict):
  - task_id          str
  - status           str ("done" | "escalated")
  - review_summary   str  human-readable review result (structural + synthesis if available)
  - endorsed         list[str]
  - flags            list[str]
  - artifact_path    str
  - synthesis        str | None  (None if synthesis skipped or failed)
  - writebacks       list of vault writeback entries for AOR Stage 7

AOR engine registration:
  _handlers["hermes_review_execute"] = run_hermes_review_execute

Public API:
    run_hermes_review_execute(inputs, vault_root) -> dict
    WorkflowExecutionError
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.execution_adapters.execute import execute_synthesis


class WorkflowExecutionError(Exception):
    """Raised when the review execution workflow cannot complete."""


# ── LLM synthesis ─────────────────────────────────────────────────────────────

_SYNTHESIS_PROMPT_TEMPLATE = """\
You are Hermes, the review runtime in the ChaseOS agent coordination system.

You have completed a structural analysis of an artifact. Your task is to write a concise \
synthesis (2–3 short paragraphs) that:
1. Interprets what the structural findings mean for artifact quality
2. Highlights the most important issues or strengths
3. Gives a clear overall quality assessment

Keep the tone direct and operational. This goes into the coordination bus result packet.

--- REVIEW REQUEST ---
{request}

--- ARTIFACT PATH ---
{artifact_path}

--- STRUCTURAL FINDINGS ---
Endorsed: {endorsed}
Flags: {flags}

--- ARTIFACT CONTENT (first 3000 chars) ---
{content_excerpt}
"""


def _execute_synthesis(
    *,
    request: str,
    artifact_path: str,
    endorsed: list[str],
    flags: list[str],
    artifact_content: str | None,
    vault_root: str | Path | None = None,
) -> str | None:
    """
    Produce a prose synthesis of the structural review through the shared adapter.

    Reads ANTHROPIC_API_KEY from the environment — raises nothing if missing, just returns None.
    Fail-open: any exception → return None. The structural review stands alone.
    """
    content_excerpt = (artifact_content or "")[:3000]
    prompt_user = _SYNTHESIS_PROMPT_TEMPLATE.format(
        request=request,
        artifact_path=artifact_path,
        endorsed=", ".join(endorsed) if endorsed else "none",
        flags=", ".join(flags) if flags else "none",
        content_excerpt=content_excerpt,
    )

    try:
        result = execute_synthesis(
            prompt_system=(
                "You are Hermes, the ChaseOS review runtime. Produce concise, "
                "operational prose that interprets the structural review. Do not "
                "invent facts beyond the provided request, artifact path, findings, "
                "and excerpt."
            ),
            prompt_user=prompt_user,
            execution_adapter="hermes",
            vault_root=Path(vault_root) if vault_root is not None else Path.cwd(),
        )
    except Exception:
        return None
    text = result.text.strip()
    return text or None


# Artifacts outside this scope are an escalation condition.
_REVIEW_SCOPE_PREFIXES = (
    "07_LOGS/Operator-Briefs/",
    "07_LOGS/SBP-Runs/",
    "07_LOGS/Build-Logs/",
    "07_LOGS/Agent-Activity/",
    "runtime/agent_bus/",
    "runtime/workflows/",
    "runtime/schedules/",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _artifact_in_scope(artifact_path: str) -> bool:
    """Return True if artifact_path starts with one of the allowed review scope prefixes."""
    normalized = artifact_path.replace("\\", "/").lstrip("/")
    return any(normalized.startswith(prefix) for prefix in _REVIEW_SCOPE_PREFIXES)


def _produce_review(
    *,
    request: str,
    artifact_path: str,
    artifact_content: str | None,
    synthesize: bool = False,
    vault_root: str | Path | None = None,
) -> dict[str, Any]:
    """
    Structural review of an artifact, with optional LLM synthesis.

    Returns dict with:
      summary: str   (structural checks + synthesis if available)
      endorsed: list[str]
      flags: list[str]
      synthesis: str | None
    """
    import re

    endorsed: list[str] = []
    flags: list[str] = []
    lines: list[str] = []

    if artifact_content is None:
        flags.append("Artifact not readable — path may not exist or is outside review scope.")
        summary = (
            f"Hermes review INCOMPLETE — artifact at `{artifact_path}` could not be read. "
            f"Request was: {request}"
        )
        return {"summary": summary, "endorsed": endorsed, "flags": flags, "synthesis": None}

    content = artifact_content
    word_count = len(content.split())

    # Structural checks
    if word_count < 10:
        flags.append(f"Artifact appears very short ({word_count} words) — may be incomplete.")
    else:
        endorsed.append(f"Artifact present and non-empty ({word_count} words).")

    has_headings = any(line.strip().startswith("#") for line in content.splitlines())
    if has_headings:
        endorsed.append("Artifact has markdown structure (headings present).")
    else:
        flags.append("No markdown headings detected — structure may be flat or non-standard.")

    has_date = bool(re.search(r"\d{4}-\d{2}-\d{2}", content))
    if has_date:
        endorsed.append("Artifact contains a date marker.")
    else:
        flags.append("No date marker (YYYY-MM-DD) found in artifact.")

    if word_count > 8000:
        flags.append(f"Artifact is long ({word_count} words) — may need operator summary pass.")

    # Check: frontmatter present (YAML/markdown convention)
    has_frontmatter = content.lstrip().startswith("---")
    if has_frontmatter:
        endorsed.append("Artifact has frontmatter block.")

    status_word = "PASS" if not flags else ("CONDITIONAL PASS" if endorsed else "FLAGGED")

    lines.append(f"## Hermes Review — {status_word}")
    lines.append(f"**Artifact:** `{artifact_path}`")
    lines.append(f"**Request:** {request}")
    lines.append("")
    if endorsed:
        lines.append("### Endorsed")
        lines.extend(f"- {e}" for e in endorsed)
        lines.append("")
    if flags:
        lines.append("### Flags")
        lines.extend(f"- {f}" for f in flags)
        lines.append("")
    lines.append(f"**Verdict:** {status_word} — {len(endorsed)} endorsed, {len(flags)} flagged.")

    # LLM synthesis — fail-open
    synthesis: str | None = None
    if synthesize:
        synthesis = _execute_synthesis(
            request=request,
            artifact_path=artifact_path,
            endorsed=endorsed,
            flags=flags,
            artifact_content=artifact_content,
            vault_root=vault_root,
        )
        if synthesis:
            lines.append("")
            lines.append("### Synthesis")
            lines.append(synthesis)

    summary = "\n".join(lines)
    return {"summary": summary, "endorsed": endorsed, "flags": flags, "synthesis": synthesis}


def _extract_artifact_path(task_data: dict | None) -> str | None:
    """Parse artifact_path from task notes field."""
    if task_data is None:
        return None
    notes = task_data.get("notes") or ""
    for line in notes.splitlines():
        line = line.strip()
        if line.startswith("artifact_path:"):
            return line.split(":", 1)[1].strip() or None
    return None


def _build_audit_content(
    *,
    task_id: str,
    artifact_path: str,
    endorsed: list[str],
    flags: list[str],
    review_summary: str,
    synthesis: str | None,
    run_iso: str,
) -> str:
    synthesis_block = f"\n## Synthesis\n\n{synthesis}\n" if synthesis else ""
    return f"""---
type: agent-activity
workflow: hermes_review_execute
task_id: {task_id}
runtime: Hermes
date: {run_iso}
synthesis: {"yes" if synthesis else "no"}
---

# Review Execution — {task_id}

**Artifact:** `{artifact_path}`
**Endorsed:** {len(endorsed)}
**Flags:** {len(flags)}
**Bus Status:** done

## Review Result

{review_summary}
{synthesis_block}"""


def run_hermes_review_execute(inputs: dict[str, Any], vault_root: Path | str) -> dict[str, Any]:
    """
    Claim and execute a review task from the coordination bus.

    Raises WorkflowExecutionError on unrecoverable errors.
    Escalation conditions (artifact out of scope, task not found) raise WorkflowExecutionError
    and also post an escalation notice to the bus before raising.
    """
    from runtime.agent_bus.bus import list_tasks, claim_task, update_task_status

    root = Path(vault_root)
    run_iso = _now_iso()
    today = _now_date()

    task_id_input = inputs.get("task_id")
    synthesize = bool(inputs.get("synthesize", False))  # explicit opt-in only — C-2
    runtime_instance_id = inputs.get("runtime_instance_id") or None

    # ── 1. Find the task ──────────────────────────────────────────────────────
    if task_id_input:
        task_id = str(task_id_input).strip()
        # Verify it exists and is addressable to Hermes
        all_tasks = list_tasks(root)
        task_data = next((t for t in all_tasks if t["task_id"] == task_id), None)
        if task_data is None:
            raise WorkflowExecutionError(f"Task '{task_id}' not found on coordination bus.")
        if task_data.get("recipient") != "Hermes":
            raise WorkflowExecutionError(
                f"Task '{task_id}' is addressed to '{task_data.get('recipient')}', not Hermes."
            )
    else:
        open_tasks = list_tasks(root, recipient="Hermes", status="open")
        if not open_tasks:
            return {
                "task_id": None,
                "status": "no_task",
                "review_summary": "No open review tasks addressed to Hermes on the coordination bus.",
                "endorsed": [],
                "flags": [],
                "artifact_path": "",
                "synthesis": None,
                "writebacks": [],
            }
        task_data = open_tasks[0]
        task_id = task_data["task_id"]

    # ── 2. Claim ──────────────────────────────────────────────────────────────
    claim_result = claim_task(
        root,
        task_id=task_id,
        runtime="Hermes",
        runtime_instance_id=runtime_instance_id,
    )
    if not claim_result.get("claimed"):
        raise WorkflowExecutionError(
            f"Failed to claim task '{task_id}': {claim_result.get('reason', 'unknown')}"
        )

    # Re-fetch task data after claim (status updated)
    all_tasks = list_tasks(root)
    task_data = next((t for t in all_tasks if t["task_id"] == task_id), task_data)

    # ── 3. Mark in_progress ───────────────────────────────────────────────────
    update_task_status(
        root,
        task_id=task_id,
        runtime="Hermes",
        status="in_progress",
        event_type="started",
        message="Hermes: review started — reading artifact.",
    )

    # ── 4. Resolve artifact path and scope check ──────────────────────────────
    artifact_path = _extract_artifact_path(task_data) or ""
    artifact_content: str | None = None

    if artifact_path:
        if not _artifact_in_scope(artifact_path):
            # Escalation — artifact outside review scope
            escalation_msg = (
                f"Hermes escalation: artifact_path '{artifact_path}' is outside the review role "
                f"card scope. Permitted prefixes: {list(_REVIEW_SCOPE_PREFIXES)}. "
                "Task marked escalated — operator intervention required."
            )
            update_task_status(
                root,
                task_id=task_id,
                runtime="Hermes",
                status="blocked",
                event_type="blocked",
                message=escalation_msg,
            )
            raise WorkflowExecutionError(escalation_msg)

        full_path = root / artifact_path
        if full_path.exists():
            try:
                artifact_content = full_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                artifact_content = None
        # artifact_content remaining None → review flags it

    # ── 5. Produce structural review + optional LLM synthesis ─────────────────
    request_text = task_data.get("request", "") if task_data else ""
    review = _produce_review(
        request=request_text,
        artifact_path=artifact_path,
        artifact_content=artifact_content,
        synthesize=synthesize,
        vault_root=root,
    )

    # ── 6. Post result to bus (done) ──────────────────────────────────────────
    update_task_status(
        root,
        task_id=task_id,
        runtime="Hermes",
        status="done",
        event_type="result_attached",
        message=review["summary"],
    )

    # ── 7. Build audit writeback ──────────────────────────────────────────────
    audit_filename = f"{today}-hermes-review-execute-{task_id[:12]}.md"
    audit_path = f"07_LOGS/Agent-Activity/{audit_filename}"
    audit_content = _build_audit_content(
        task_id=task_id,
        artifact_path=artifact_path,
        endorsed=review["endorsed"],
        flags=review["flags"],
        review_summary=review["summary"],
        synthesis=review["synthesis"],
        run_iso=run_iso,
    )

    return {
        "task_id": task_id,
        "status": "done",
        "review_summary": review["summary"],
        "endorsed": review["endorsed"],
        "flags": review["flags"],
        "artifact_path": artifact_path,
        "synthesis": review["synthesis"],
        "writebacks": [
            {"path": audit_path, "content": audit_content},
        ],
    }
