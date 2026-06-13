"""Controlled source-shape proof for Studio Capture to Markdown.

The proof runs against a disposable scratch vault through the Studio
application programming interface. It covers source shapes that were still open
in release hardening without reading personal browser, Discord, clipboard, or
screen state.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
from typing import Any


MODEL_VERSION = "studio.capture_markdown_source_shape_matrix_proof.v1"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS/Studio-Graph-Views")
DEFAULT_SCRATCH_ROOT = Path(".tmp/cmsm")


def build_capture_markdown_source_shape_matrix_proof(
    vault_root: str | Path,
    *,
    scratch_root: str | Path | None = None,
    evidence_root: str | Path | None = None,
    evidence_slug: str | None = None,
    write_evidence: bool = False,
) -> dict[str, Any]:
    """Run the controlled source-shape matrix and optionally write evidence."""

    vault = Path(vault_root).resolve()
    run_id = _run_id()
    scratch = _resolve_scratch_root(vault, scratch_root, run_id)
    evidence_paths: dict[str, str] = {}
    cases: list[dict[str, Any]] = []
    scratch_removed = False

    if scratch.exists():
        shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, exist_ok=True)

    try:
        _seed_scratch_vault(scratch, run_id)
        cases.extend(_run_preview_and_save_cases(scratch, run_id))
        cases.append(_run_secret_like_save_block_case(scratch, run_id))
        cases.append(_run_needs_redaction_downstream_block_case(scratch, run_id))
        cases.append(_run_duplicate_save_block_case(scratch, run_id))
        forbidden_writes = _detect_forbidden_downstream_writes(scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
        _remove_empty_scratch_parents(scratch.parent, stop=vault)
        scratch_removed = not scratch.exists()

    summary = _build_summary(cases, scratch_removed=scratch_removed)
    ok = bool(summary["all_cases_passed"] and scratch_removed and not forbidden_writes)
    report: dict[str, Any] = {
        "ok": ok,
        "status": "capture_markdown_source_shape_matrix_verified"
        if ok
        else "capture_markdown_source_shape_matrix_failed",
        "model_version": MODEL_VERSION,
        "run_id": run_id,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "scratch_workspace": {
            "path": str(scratch),
            "removed_after_run": scratch_removed,
            "used_disposable_vault": True,
        },
        "authority": {
            "uses_studio_application_programming_interface": True,
            "reads_personal_browser_state": False,
            "reads_clipboard": False,
            "captures_screen_pixels": False,
            "calls_discord": False,
            "calls_model_provider": False,
            "writes_selected_vault": bool(write_evidence),
            "selected_vault_write_scope": "evidence_only" if write_evidence else "none",
            "canonical_mutation_allowed": False,
            "graph_index_mutation_allowed": False,
            "source_intelligence_core_ingestion_allowed": False,
            "agent_orchestration_runtime_dispatch_allowed": False,
        },
        "summary": summary,
        "cases": cases,
        "forbidden_downstream_writes": forbidden_writes,
        "evidence": evidence_paths,
    }
    if write_evidence:
        slug = evidence_slug or f"{run_id}-capture-markdown-source-shape-matrix"
        evidence_paths = write_capture_markdown_source_shape_matrix_evidence(
            vault,
            report,
            evidence_slug=slug,
            evidence_root=evidence_root,
        )
        report["evidence"] = evidence_paths
        report["writes_performed"] = True
    else:
        report["writes_performed"] = False
    return report


def write_capture_markdown_source_shape_matrix_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str,
    evidence_root: str | Path | None = None,
) -> dict[str, str]:
    vault = Path(vault_root).resolve()
    root = Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT
    root = root if root.is_absolute() else vault / root
    root.mkdir(parents=True, exist_ok=True)
    safe_slug = _safe_slug(evidence_slug)
    json_path = root / f"{safe_slug}.json"
    markdown_path = root / f"{safe_slug}.md"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True, default=str),
        encoding="utf-8",
    )
    markdown_path.write_text(_markdown_report(report), encoding="utf-8")
    return {
        "json_path": _rel(json_path, vault),
        "markdown_path": _rel(markdown_path, vault),
    }


def _run_preview_and_save_cases(scratch: Path, run_id: str) -> list[dict[str, Any]]:
    cases = [
        {
            "id": "clean_article_text",
            "label": "Clean article-style manual text",
            "payload": _manual_payload(
                run_id,
                title="Clean",
                text=(
                    "Capture to Markdown clean article fixture.\n\n"
                    "The operator wants a readable source note with normal punctuation, "
                    "headings, and paragraphs preserved for review."
                ),
            ),
            "expected_phrases": ["clean article fixture", "normal punctuation"],
        },
        {
            "id": "long_source_text",
            "label": "Long source text",
            "payload": _manual_payload(
                run_id,
                title="Long",
                text=_long_source_text(run_id),
            ),
            "expected_phrases": [
                "Long source section 001",
                "Long source section 120",
            ],
            "minimum_markdown_chars": 9000,
        },
        {
            "id": "sparse_source_text",
            "label": "Sparse source text",
            "payload": _manual_payload(
                run_id,
                title="Sparse",
                text="Sparse capture fixture.\n\nOne sentence.",
            ),
            "expected_phrases": ["Sparse capture fixture", "One sentence"],
        },
        {
            "id": "table_code_text",
            "label": "Table and code text",
            "payload": _manual_payload(
                run_id,
                title="Table Code",
                text=(
                    "| Field | Value |\n"
                    "| --- | --- |\n"
                    "| Capture | Markdown |\n\n"
                    "```python\n"
                    "def capture_value():\n"
                    "    return 'table-code-fixture'\n"
                    "```"
                ),
            ),
            "expected_phrases": ["| Capture | Markdown |", "def capture_value()"],
        },
        {
            "id": "local_markdown_file",
            "label": "Vault Markdown file",
            "payload": {
                "source_mode": "local_text_file",
                "profile": "research_note",
                "title": "Local File",
                "file_path": "fixtures/local-source.md",
                "user_intent": "controlled source-shape file proof",
            },
            "expected_phrases": ["Local Markdown source fixture", "file-based capture"],
        },
        {
            "id": "saved_html_file",
            "label": "Saved page file",
            "payload": {
                "source_mode": "saved_html_file",
                "profile": "research_note",
                "title": "Saved Page",
                "file_path": "fixtures/saved-page.html",
                "source_url": "https://example.test/source-shape/saved-page",
                "user_intent": "controlled saved page proof",
            },
            "expected_phrases": ["Saved Page Fixture", "saved page body"],
        },
        {
            "id": "controlled_browser_artifact",
            "label": "Controlled browser artifact",
            "payload": {
                "source_mode": "controlled_html_artifact",
                "profile": "research_note",
                "title": "Browser Art",
                "file_path": "07_LOGS/Browser-Runs/source-shape/controlled.html",
                "source_url": "https://example.test/source-shape/controlled",
                "allowed_origin": "https://example.test",
                "user_intent": "controlled browser artifact proof",
            },
            "expected_phrases": ["Controlled Browser Fixture", "artifact body"],
        },
    ]
    return [_run_preview_save_case(scratch, case) for case in cases]


def _run_preview_save_case(scratch: Path, case: dict[str, Any]) -> dict[str, Any]:
    from runtime.studio.shell.api import StudioAPI

    api = StudioAPI(str(scratch))
    preview_response = api.preview_capture_to_markdown(case["payload"])
    preview_data = preview_response.get("data") or {}
    save_response = api.save_capture_to_markdown(case["payload"])
    save_data = save_response.get("data") or {}
    markdown = str(preview_data.get("markdown") or "")
    expected_phrases = list(case.get("expected_phrases") or [])
    expected_phrases_present = all(phrase in markdown for phrase in expected_phrases)
    minimum_markdown_chars = int(case.get("minimum_markdown_chars") or 0)
    content_path = Path(str(save_data.get("content_path") or ""))
    sidecar_path = Path(str(save_data.get("sidecar_path") or ""))
    packet_path = Path(str(save_data.get("visual_capture_packet_path") or ""))
    sidecar = _read_json(sidecar_path) if sidecar_path.exists() else {}
    visual_capture = (
        (sidecar.get("extra_metadata") or {}).get("visual_capture")
        if isinstance(sidecar.get("extra_metadata"), dict)
        else {}
    )
    checks = {
        "preview_ok": bool(preview_response.get("ok") and preview_data.get("preview_ready")),
        "preview_write_free": preview_data.get("write_performed") is False,
        "expected_phrases_present": expected_phrases_present,
        "minimum_markdown_length_met": len(markdown) >= minimum_markdown_chars,
        "save_ok": bool(save_response.get("ok") and save_data.get("status") == "raw_ingested"),
        "save_wrote_quarantine_artifacts": bool(
            save_data.get("write_performed")
            and content_path.exists()
            and sidecar_path.exists()
            and packet_path.exists()
        ),
        "content_under_quarantine": _is_relative_to(
            content_path, scratch / "03_INPUTS" / "00_QUARANTINE"
        ),
        "canonical_not_mutated": visual_capture.get("canonical_status") == "not_promoted",
        "source_package_not_written": sidecar.get("source_package_status") == "not-ingested",
        "agent_orchestration_runtime_not_queued": (
            visual_capture.get("aor_queue_status") == "not_queued"
        ),
        "source_intelligence_core_not_ingested": (
            visual_capture.get("sic_ingestion_status", "not_ingested") in {"", "not_ingested"}
        ),
        "provider_not_called": (
            ((visual_capture.get("authority") or {}).get("provider_call_allowed") is False)
            if isinstance(visual_capture, dict)
            else False
        ),
    }
    return {
        "id": case["id"],
        "label": case["label"],
        "source_mode": str(case["payload"].get("source_mode") or ""),
        "ok": all(checks.values()),
        "checks": checks,
        "preview": {
            "surface": preview_response.get("surface") or "",
            "status": preview_data.get("status") or "",
            "markdown_char_count": len(markdown),
            "save_allowed": bool(preview_data.get("save_allowed")),
            "blockers": list(preview_data.get("blockers") or []),
        },
        "save": {
            "surface": save_response.get("surface") or "",
            "status": save_data.get("status") or "",
            "write_performed": bool(save_data.get("write_performed")),
            "is_duplicate": bool(save_data.get("is_duplicate")),
            "content_path": _rel(content_path, scratch) if content_path.exists() else "",
            "sidecar_path": _rel(sidecar_path, scratch) if sidecar_path.exists() else "",
            "visual_capture_packet_path": _rel(packet_path, scratch) if packet_path.exists() else "",
        },
    }


def _run_secret_like_save_block_case(scratch: Path, run_id: str) -> dict[str, Any]:
    from runtime.studio.shell.api import StudioAPI

    api = StudioAPI(str(scratch))
    before_files = _file_count(scratch / "03_INPUTS" / "00_QUARANTINE")
    payload = _manual_payload(
        run_id,
        title="Secret Block",
        text="api_key=OPENAI_API_KEY_FAKE_CAPTURE_MARKDOWN_SECRET_BLOCK_FIXTURE",
    )
    preview_response = api.preview_capture_to_markdown(payload)
    save_response = api.save_capture_to_markdown(payload)
    after_files = _file_count(scratch / "03_INPUTS" / "00_QUARANTINE")
    preview_data = preview_response.get("data") or {}
    save_data = save_response.get("data") or {}
    checks = {
        "preview_ok": bool(preview_response.get("ok")),
        "preview_blocks_save": preview_data.get("save_allowed") is False,
        "save_fails_closed": save_response.get("ok") is False,
        "save_status_blocked": save_data.get("status") == "blocked_secret_like",
        "no_quarantine_write": before_files == after_files,
        "blocker_explained": "secret_or_credential_indicator_present"
        in list(save_data.get("blockers") or []),
    }
    return {
        "id": "secret_like_save_block",
        "label": "Secret-like input save block",
        "source_mode": "manual_text",
        "ok": all(checks.values()),
        "checks": checks,
        "preview": {
            "surface": preview_response.get("surface") or "",
            "status": preview_data.get("status") or "",
            "save_allowed": bool(preview_data.get("save_allowed")),
            "blockers": list(preview_data.get("blockers") or []),
        },
        "save": {
            "surface": save_response.get("surface") or "",
            "status": save_data.get("status") or "",
            "write_performed": bool(save_data.get("write_performed")),
            "blockers": list(save_data.get("blockers") or []),
        },
    }


def _run_needs_redaction_downstream_block_case(scratch: Path, run_id: str) -> dict[str, Any]:
    from runtime.studio.shell.api import StudioAPI

    api = StudioAPI(str(scratch))
    save_response = api.save_capture_to_markdown(
        _manual_payload(
            run_id,
            title="Needs Redact",
            text="Needs redaction review path fixture.",
        )
    )
    save_data = save_response.get("data") or {}
    review_response = api.review_capture_to_markdown(
        {
            "sidecar_path": save_data.get("sidecar_path") or "",
            "decision": "needs-redaction",
            "review_note": "controlled needs-redaction proof",
        }
    )
    preview_response = api.preview_capture_to_markdown_source_pack_approval(
        {
            "sidecar_path": save_data.get("sidecar_path") or "",
            "reviewed_by": "Codex",
        }
    )
    review_data = review_response.get("data") or {}
    preview_data = preview_response.get("data") or {}
    checks = {
        "save_ok": bool(save_response.get("ok") and save_data.get("status") == "raw_ingested"),
        "review_marks_needs_redaction": bool(
            review_response.get("ok") and review_data.get("new_status") == "needs-redaction"
        ),
        "review_does_not_rewrite_content": review_data.get("content_write_performed") is False,
        "source_pack_preview_blocked": preview_data.get("ok") is False
        and preview_data.get("status") == "blocked_before_source_pack_write_approval_preview",
        "downstream_write_not_performed": preview_data.get("write_performed") is False,
        "source_pack_write_not_performed": preview_data.get("source_pack_write_performed") is False,
        "blocked_reason_present": bool(preview_data.get("blockers")),
    }
    return {
        "id": "needs_redaction_review_blocks_downstream",
        "label": "Needs-redaction review blocks downstream approval preview",
        "source_mode": "manual_text",
        "ok": all(checks.values()),
        "checks": checks,
        "review": {
            "surface": review_response.get("surface") or "",
            "status": review_data.get("status") or "",
            "new_status": review_data.get("new_status") or "",
            "content_write_performed": bool(review_data.get("content_write_performed")),
        },
        "source_pack_approval_preview": {
            "surface": preview_response.get("surface") or "",
            "status": preview_data.get("status") or "",
            "ok": bool(preview_data.get("ok")),
            "blockers": list(preview_data.get("blockers") or []),
            "write_performed": bool(preview_data.get("write_performed")),
            "source_pack_write_performed": bool(preview_data.get("source_pack_write_performed")),
        },
    }


def _run_duplicate_save_block_case(scratch: Path, run_id: str) -> dict[str, Any]:
    from runtime.studio.shell.api import StudioAPI

    api = StudioAPI(str(scratch))
    payload = _manual_payload(
        run_id,
        title="Dup Guard",
        text="Duplicate guard source-shape fixture.",
    )
    first = api.save_capture_to_markdown(payload)
    before_files = _file_count(scratch / "03_INPUTS" / "00_QUARANTINE")
    second = api.save_capture_to_markdown(payload)
    after_files = _file_count(scratch / "03_INPUTS" / "00_QUARANTINE")
    first_data = first.get("data") or {}
    second_data = second.get("data") or {}
    checks = {
        "first_save_ok": bool(first.get("ok") and first_data.get("status") == "raw_ingested"),
        "second_save_ok": bool(second.get("ok")),
        "second_is_duplicate": second_data.get("is_duplicate") is True,
        "second_status_duplicate": second_data.get("status") == "duplicate",
        "second_write_blocked": second_data.get("write_performed") is False,
        "no_second_quarantine_file": before_files == after_files,
    }
    return {
        "id": "duplicate_save_blocks_second_write",
        "label": "Duplicate save blocks second write",
        "source_mode": "manual_text",
        "ok": all(checks.values()),
        "checks": checks,
        "first_save": {
            "surface": first.get("surface") or "",
            "status": first_data.get("status") or "",
            "write_performed": bool(first_data.get("write_performed")),
        },
        "second_save": {
            "surface": second.get("surface") or "",
            "status": second_data.get("status") or "",
            "write_performed": bool(second_data.get("write_performed")),
            "is_duplicate": bool(second_data.get("is_duplicate")),
            "duplicate_of": second_data.get("duplicate_of") or "",
        },
    }


def _build_summary(cases: list[dict[str, Any]], *, scratch_removed: bool) -> dict[str, Any]:
    passed = [case for case in cases if case.get("ok")]
    source_modes = sorted({str(case.get("source_mode") or "") for case in cases if case.get("source_mode")})
    return {
        "case_count": len(cases),
        "passed_case_count": len(passed),
        "failed_case_count": len(cases) - len(passed),
        "all_cases_passed": len(passed) == len(cases),
        "source_modes_covered": source_modes,
        "clean_article_text_verified": _case_ok(cases, "clean_article_text"),
        "long_source_text_verified": _case_ok(cases, "long_source_text"),
        "sparse_source_text_verified": _case_ok(cases, "sparse_source_text"),
        "table_code_text_verified": _case_ok(cases, "table_code_text"),
        "local_markdown_file_verified": _case_ok(cases, "local_markdown_file"),
        "saved_html_file_verified": _case_ok(cases, "saved_html_file"),
        "controlled_browser_artifact_verified": _case_ok(cases, "controlled_browser_artifact"),
        "secret_like_save_block_verified": _case_ok(cases, "secret_like_save_block"),
        "needs_redaction_downstream_block_verified": _case_ok(
            cases, "needs_redaction_review_blocks_downstream"
        ),
        "duplicate_save_block_verified": _case_ok(cases, "duplicate_save_blocks_second_write"),
        "scratch_workspace_removed": scratch_removed,
    }


def _seed_scratch_vault(scratch: Path, run_id: str) -> None:
    local_file = scratch / "fixtures" / "local-source.md"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_text(
        "# Local Markdown source fixture\n\nThis file-based capture fixture proves Markdown file input.",
        encoding="utf-8",
    )
    saved_html = scratch / "fixtures" / "saved-page.html"
    saved_html.write_text(
        "<html><head><title>Saved Page Fixture</title></head><body>"
        "<main><h1>Saved Page Fixture</h1><p>This saved page body belongs to "
        f"source-shape run {run_id}.</p></main></body></html>",
        encoding="utf-8",
    )
    controlled = scratch / "07_LOGS" / "Browser-Runs" / "source-shape" / "controlled.html"
    controlled.parent.mkdir(parents=True, exist_ok=True)
    controlled.write_text(
        "<html><head><title>Controlled Browser Fixture</title></head><body>"
        "<main><h1>Controlled Browser Fixture</h1><p>The controlled artifact body "
        f"belongs to source-shape run {run_id}.</p></main></body></html>",
        encoding="utf-8",
    )
    _seed_downstream_contracts(scratch)


def _seed_downstream_contracts(scratch: Path) -> None:
    now = scratch / "00_HOME" / "Now.md"
    now.parent.mkdir(parents=True, exist_ok=True)
    now.write_text(
        "# Now\n\n## Current Phase\nPhase 9 controlled source-shape fixture\n",
        encoding="utf-8",
    )
    workflow = scratch / "runtime" / "workflows" / "registry" / "source_pack_builder.yaml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "\n".join(
            [
                "id: source_pack_builder",
                "workflow_id: source_pack_builder",
                "name: Source Pack Builder",
                "version: '1.0'",
                "status: active",
                "task_type: source-pack-builder",
                "permission_ceiling: acquisition_pack_only",
                "writeback_targets:",
                "  - runtime/acquisition/packs/",
                "  - 07_LOGS/Acquisition-Packs/",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    task_table = scratch / "runtime" / "aor" / "task_type_table.yaml"
    task_table.parent.mkdir(parents=True, exist_ok=True)
    task_table.write_text(
        "task_types:\n"
        "  - id: source-pack-builder\n"
        "    permission_ceiling: acquisition_pack_only\n"
        "    notes: no canonical mutations; canonical mutation requested must escalate\n",
        encoding="utf-8",
    )
    schema = scratch / "runtime" / "source_intelligence" / "schemas" / "source_package_schema.md"
    schema.parent.mkdir(parents=True, exist_ok=True)
    schema.write_text(
        "# Source Package Schema\n\nRequired controlled proof fixture fields.\n",
        encoding="utf-8",
    )
    (scratch / "runtime" / "source_intelligence" / "workspaces").mkdir(
        parents=True,
        exist_ok=True,
    )


def _detect_forbidden_downstream_writes(scratch: Path) -> list[str]:
    forbidden_roots = [
        "runtime/acquisition/packs",
        "07_LOGS/Acquisition-Packs",
        "02_KNOWLEDGE",
        "runtime/source_intelligence/workspaces",
    ]
    found: list[str] = []
    for relative in forbidden_roots:
        root = scratch / relative
        if not root.exists():
            continue
        found.extend(_rel(path, scratch) for path in root.rglob("*") if path.is_file())
    return sorted(found)


def _manual_payload(run_id: str, *, title: str, text: str) -> dict[str, Any]:
    return {
        "source_mode": "manual_text",
        "profile": "research_note",
        "title": title,
        "raw_text": text,
        "source_url": f"https://example.test/source-shape/{_safe_slug(title)}",
        "user_intent": "controlled source-shape matrix proof",
        "structured_notes": "- keep capture in raw quarantine for operator review",
        "generated_summary": "Controlled source-shape proof fixture.",
        "generated_interpretation": "No downstream writeback should happen during capture.",
    }


def _long_source_text(run_id: str) -> str:
    lines = [
        f"Long source section {index:03d}: run {run_id} keeps Markdown capture stable across a long page body."
        for index in range(1, 121)
    ]
    return "\n\n".join(lines)


def _case_ok(cases: list[dict[str, Any]], case_id: str) -> bool:
    return any(case.get("id") == case_id and case.get("ok") for case in cases)


def _file_count(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file())


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _resolve_scratch_root(vault: Path, scratch_root: str | Path | None, run_id: str) -> Path:
    if scratch_root:
        path = Path(scratch_root)
        return (path if path.is_absolute() else vault / path).resolve()
    return (vault / DEFAULT_SCRATCH_ROOT / run_id).resolve()


def _remove_empty_scratch_parents(path: Path, *, stop: Path) -> None:
    current = path.resolve()
    stop_resolved = stop.resolve()
    while current != stop_resolved and _is_relative_to(current, stop_resolved):
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Capture to Markdown Source-Shape Matrix Proof",
        "",
        f"- Status: {report.get('status')}",
        f"- Run: {report.get('run_id')}",
        f"- Generated: {report.get('generated_at_utc')}",
        f"- Cases passed: {(report.get('summary') or {}).get('passed_case_count')} / {(report.get('summary') or {}).get('case_count')}",
        f"- Scratch removed: {(report.get('summary') or {}).get('scratch_workspace_removed')}",
        "",
        "## Cases",
    ]
    for case in report.get("cases") or []:
        if not isinstance(case, dict):
            continue
        lines.append(
            f"- {'PASS' if case.get('ok') else 'FAIL'} - {case.get('id')}: {case.get('label')}"
        )
    if report.get("forbidden_downstream_writes"):
        lines.extend(["", "## Forbidden Downstream Writes"])
        lines.extend(f"- {path}" for path in report.get("forbidden_downstream_writes") or [])
    return "\n".join(lines) + "\n"


def _safe_slug(value: str) -> str:
    raw = str(value or "").strip().lower()
    chars = [char if char.isalnum() else "-" for char in raw]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug[:120] or "capture-markdown-source-shape-matrix"


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a controlled Studio Capture to Markdown source-shape matrix proof.",
    )
    parser.add_argument("--vault-root", default=".", help="Workspace vault root.")
    parser.add_argument("--scratch-root", default=None, help="Optional scratch vault path.")
    parser.add_argument("--evidence-root", default=None, help="Vault-relative evidence root.")
    parser.add_argument("--evidence-slug", default=None, help="Evidence file slug.")
    parser.add_argument("--write-evidence", action="store_true", help="Write JSON and Markdown evidence.")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Print the full report as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_capture_markdown_source_shape_matrix_proof(
        args.vault_root,
        scratch_root=args.scratch_root,
        evidence_root=args.evidence_root,
        evidence_slug=args.evidence_slug,
        write_evidence=args.write_evidence,
    )
    if args.output_json:
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    else:
        status = "OK" if report.get("ok") else "BLOCKED"
        print(f"{status}: {report.get('status')}")
        for case in report.get("cases") or []:
            print(f"- {'PASS' if case.get('ok') else 'FAIL'} {case.get('id')}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
