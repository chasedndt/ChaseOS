"""Multi-instance fixture harness for personal context import.

The harness runs anonymized context packets through the preview writer and the
approved-preview execution proof inside isolated fixture vaults. It proves route
coverage, source-digest gating, secret blocking, and canonical-write boundaries
without writing to the operator's live vault.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any
import uuid

from runtime.studio.personal_context_import_approved_preview_execution_proof import (
    execute_personal_context_import_approved_preview_execution_proof,
)
from runtime.studio.personal_context_import_preview_writer import (
    NODE_RULES,
    build_personal_context_import_preview_writer,
    _sha256_text,
)


MODEL_VERSION = "studio.personal_context_import_multi_instance_fixture_harness.v1"
SURFACE_ID = "studio_personal_context_import_multi_instance_fixture_harness"
PASS_ID = "personal-context-import-multi-instance-fixture-harness"
STATUS = "COMPLETE / MULTI-INSTANCE FIXTURE HARNESS READY / CANONICAL WRITES BLOCKED"
FAILED_STATUS = "FAILED / MULTI-INSTANCE FIXTURE HARNESS / REVIEW REQUIRED"
NEXT_RECOMMENDED_PASS = "personal-context-import-personal-map-apply-readiness"
DEFAULT_OPERATOR_ID = "fixture-harness"

CANONICAL_TARGET_DIRS = (
    "00_HOME",
    "01_PROJECTS",
    "02_KNOWLEDGE",
    "06_AGENTS",
)


@dataclass(frozen=True)
class _Fixture:
    fixture_id: str
    label: str
    category: str
    source_text: str
    required_rule_ids: tuple[str, ...]
    expected_blockers: tuple[str, ...] = ()


POSITIVE_FIXTURES: tuple[_Fixture, ...] = (
    _Fixture(
        fixture_id="operator-technical-founder-student",
        label="Technical Founder Student",
        category="positive",
        source_text="""
Anonymized personal context export:
- Identity doctrine, discipline, values, and decision rules belong under SOUL and Principles.
- ChaseOS is the personal OS, Studio, operator runtime, agent bus, and workspace mode control layer.
- University computer science degree work includes modules and Principles of Software Engineering.
- Technical learning includes prompt engineering, agent engineering, runtime engineering, RAG, MCP, source intelligence, retrieval, and knowledge graph work.
- Language learning includes Mandarin, HSK 1, Chinese practice, and global mobility.
- Goals, routines, preferences, and personal map profile edges should be reviewed before memory apply.
""",
        required_rule_ids=(
            "identity_doctrine",
            "chaseos_architecture",
            "university_modules",
            "prompt_engineering",
            "agent_engineering",
            "runtime_engineering",
            "rag_mcp_source_intelligence",
            "language_learning_global_mobility",
            "mandarin_hsk1",
            "personal_map_candidates",
        ),
    ),
    _Fixture(
        fixture_id="creator-commerce-fitness",
        label="Creator Commerce Fitness",
        category="positive",
        source_text="""
Anonymized creator and life-domain context:
- Fitness, combat, boxing, gym, running, recovery, and physical discipline are active domains.
- Interests and hobbies include piano, geopolitics, geo politics, history, content creation, YouTube monetization, creator strategy, and personal brand.
- Networking, social capital, LinkedIn, Twitch, relationships, and network building matter.
- Hardware interests include GPU systems, Raspberry Pi, edge compute, robotics, physical AI, and future robotics.
- Full stack software engineering includes React, backend, web3, and Solana projects.
- The creator system should route to Content Creation OS and the Projects Hub.
""",
        required_rule_ids=(
            "fitness_combat_physical_discipline",
            "interests_knowledge_domains",
            "piano_interest",
            "geopolitics_history_interest",
            "content_creation_youtube_monetization",
            "networking_social_capital",
            "hardware_robotics",
            "full_stack_software_engineering",
        ),
    ),
    _Fixture(
        fixture_id="markets-security-hardware",
        label="Markets Security Hardware",
        category="positive",
        source_text="""
Anonymized applied-work context:
- Trading systems include market structure, crypto, funding rates, order flow, risk management, and indicator design.
- Cybersecurity includes bug bounty, vulnerability research, pentest thinking, security notes, and credential boundary discipline.
- Full stack work includes software engineering, React, backend services, web3, and Solana experiments.
- Hardware work includes GPU resale, Raspberry Pi automation, edge compute, robotics, and physical AI.
- Runtime engineering, agent runtimes, multi-agent workflows, tool use, and ChaseOS runtime operations should stay linked to agent engineering.
- Personal map goals, preferences, routines, and habits should be candidates only until reviewed.
""",
        required_rule_ids=(
            "trading_systems_market_ops",
            "cybersecurity_bug_bounty",
            "full_stack_software_engineering",
            "hardware_robotics",
            "runtime_engineering",
            "agent_engineering",
            "personal_map_candidates",
        ),
    ),
)

NEGATIVE_FIXTURES: tuple[_Fixture, ...] = (
    _Fixture(
        fixture_id="secret-like-blocker",
        label="Secret-Like Blocker",
        category="negative",
        source_text=(
            "An anonymized context packet mentions Mandarin and project goals, "
            "but also includes api_key=fixture-secret-value-123456789."
        ),
        required_rule_ids=(),
        expected_blockers=("secret_or_credential_indicator_present",),
    ),
)


def _fixture_public(fixture: _Fixture) -> dict[str, Any]:
    return {
        "fixture_id": fixture.fixture_id,
        "label": fixture.label,
        "category": fixture.category,
        "source_digest_sha256": _sha256_text(fixture.source_text),
        "source_text_included": False,
        "required_rule_ids": list(fixture.required_rule_ids),
        "expected_blockers": list(fixture.expected_blockers),
    }


def _approval_statement(digest: str) -> str:
    return f"approve personal context import preview execution {digest}"


def _canonical_write_violations(fixture_root: Path) -> list[str]:
    return [item for item in CANONICAL_TARGET_DIRS if (fixture_root / item).exists()]


def _json_does_not_include_source(payload: dict[str, Any], source_text: str) -> bool:
    encoded = json.dumps(payload, sort_keys=True)
    stripped = source_text.strip()
    return bool(stripped) and stripped not in encoded


def _safe_run_root(fixture_root: str | Path | None) -> tuple[Path, bool]:
    if fixture_root is not None:
        root = (Path(fixture_root).resolve() / f"r{uuid.uuid4().hex[:4]}").resolve()
        root.mkdir(parents=True, exist_ok=False)
        return root, False

    preferred_parent = Path("C:/tmp")
    parent = preferred_parent if preferred_parent.exists() else Path(tempfile.gettempdir())
    try:
        root = Path(tempfile.mkdtemp(prefix="r", dir=str(parent))).resolve()
    except OSError:
        root = Path(tempfile.mkdtemp(prefix="r")).resolve()
    return root, True


def _fixture_vault_path(run_root: Path, fixture: _Fixture) -> Path:
    short_name = _sha256_text(fixture.fixture_id)[:5]
    return run_root / f"f{short_name}"


def _run_positive_fixture(run_root: Path, fixture: _Fixture, operator_id: str) -> dict[str, Any]:
    fixture_vault = _fixture_vault_path(run_root, fixture)
    fixture_vault.mkdir(parents=True, exist_ok=True)

    preview = build_personal_context_import_preview_writer(
        fixture_vault,
        source_text=fixture.source_text,
        source_label=fixture.fixture_id,
        operator_id=operator_id,
        write_approval=False,
    )
    digest = str((preview.get("digest_proof") or {}).get("import_preview_digest") or "")
    proposals = (preview.get("proposal_packet_preview") or {}).get("node_proposals") or []
    present_rule_ids = sorted({str(item.get("rule_id")) for item in proposals if item.get("rule_id")})
    missing_required = [rule_id for rule_id in fixture.required_rule_ids if rule_id not in present_rule_ids]

    queued = build_personal_context_import_preview_writer(
        fixture_vault,
        source_text=fixture.source_text,
        source_label=fixture.fixture_id,
        expected_import_preview_digest=digest,
        write_approval=True,
        operator_id=operator_id,
    )
    approval_id = str((queued.get("approval_record") or {}).get("approval_id") or "")

    execution = execute_personal_context_import_approved_preview_execution_proof(
        fixture_vault,
        approval_id=approval_id,
        expected_import_preview_digest=digest,
        source_text=fixture.source_text,
        operator_approval_statement=_approval_statement(digest),
        operator_id=operator_id,
        execute=True,
    )

    canonical_violations = _canonical_write_violations(fixture_vault)
    payload_probe = {
        "preview": preview,
        "queued": queued,
        "execution": execution,
    }
    ok = (
        bool(preview.get("ok"))
        and bool(queued.get("ok"))
        and bool(execution.get("ok"))
        and not missing_required
        and not canonical_violations
        and _json_does_not_include_source(payload_probe, fixture.source_text)
    )

    return {
        "fixture_id": fixture.fixture_id,
        "category": fixture.category,
        "ok": ok,
        "preview_ok": bool(preview.get("ok")),
        "approval_request_created": bool((queued.get("summary") or {}).get("approval_request_created")),
        "execution_ok": bool(execution.get("ok")),
        "source_digest_sha256": _sha256_text(fixture.source_text),
        "import_preview_digest": digest or None,
        "approval_id": approval_id or None,
        "required_rule_ids": list(fixture.required_rule_ids),
        "matched_rule_ids": present_rule_ids,
        "missing_required_rule_ids": missing_required,
        "node_proposal_count": int((preview.get("summary") or {}).get("node_proposal_count") or 0),
        "edge_proposal_count": int((preview.get("summary") or {}).get("edge_proposal_count") or 0),
        "index_patch_target_count": int((preview.get("summary") or {}).get("index_patch_target_count") or 0),
        "artifact_count": int((execution.get("artifact_writes") or {}).get("artifact_count") or 0),
        "source_text_included_in_result": False,
        "result_does_not_echo_full_source": _json_does_not_include_source(payload_probe, fixture.source_text),
        "source_digest_matched": bool((execution.get("digest_proof") or {}).get("source_digest_matched")),
        "import_preview_digest_matched": bool((execution.get("digest_proof") or {}).get("import_preview_digest_matched")),
        "exact_once_marker_written": bool((execution.get("exact_once_marker") or {}).get("marker_written")),
        "canonical_write_violations": canonical_violations,
        "canonical_write_block_verified": not canonical_violations,
        "blocked_reasons": list(dict.fromkeys(
            list(preview.get("blocked_reasons") or [])
            + list(queued.get("blocked_reasons") or [])
            + list(execution.get("blocked_reasons") or [])
            + [f"missing_required_rule_id:{item}" for item in missing_required]
            + [f"canonical_write_violation:{item}" for item in canonical_violations]
        )),
    }


def _run_negative_fixture(run_root: Path, fixture: _Fixture, operator_id: str) -> dict[str, Any]:
    fixture_vault = _fixture_vault_path(run_root, fixture)
    fixture_vault.mkdir(parents=True, exist_ok=True)

    preview = build_personal_context_import_preview_writer(
        fixture_vault,
        source_text=fixture.source_text,
        source_label=fixture.fixture_id,
        expected_import_preview_digest="blocked-fixture",
        write_approval=True,
        operator_id=operator_id,
    )
    blockers = list(preview.get("blocked_reasons") or [])
    expected_present = all(item in blockers for item in fixture.expected_blockers)
    approval_created = bool((preview.get("summary") or {}).get("approval_request_created"))
    canonical_violations = _canonical_write_violations(fixture_vault)
    ok = (
        not preview.get("ok")
        and expected_present
        and not approval_created
        and not canonical_violations
        and _json_does_not_include_source(preview, fixture.source_text)
    )

    return {
        "fixture_id": fixture.fixture_id,
        "category": fixture.category,
        "ok": ok,
        "preview_ok_expected_false": preview.get("ok") is False,
        "source_digest_sha256": _sha256_text(fixture.source_text),
        "source_text_included_in_result": False,
        "result_does_not_echo_full_source": _json_does_not_include_source(preview, fixture.source_text),
        "expected_blockers": list(fixture.expected_blockers),
        "blocked_reasons": blockers,
        "expected_blockers_present": expected_present,
        "approval_request_created": approval_created,
        "canonical_write_violations": canonical_violations,
        "canonical_write_block_verified": not canonical_violations,
    }


def _coverage(positive_results: list[dict[str, Any]]) -> dict[str, Any]:
    all_rule_ids = sorted({str(rule["id"]) for rule in NODE_RULES})
    matched = sorted({rule_id for result in positive_results for rule_id in result.get("matched_rule_ids", [])})
    required = sorted({rule_id for fixture in POSITIVE_FIXTURES for rule_id in fixture.required_rule_ids})
    missing_required = sorted(rule_id for rule_id in required if rule_id not in matched)
    return {
        "known_rule_count": len(all_rule_ids),
        "positive_fixture_required_rule_count": len(required),
        "matched_rule_count": len(matched),
        "matched_rule_ids": matched,
        "required_rule_ids": required,
        "missing_required_rule_ids": missing_required,
        "missing_required_rule_count": len(missing_required),
        "uncovered_known_rule_ids": [rule_id for rule_id in all_rule_ids if rule_id not in matched],
    }


def build_personal_context_import_multi_instance_fixture_harness(
    vault_root: str | Path,
    *,
    fixture_root: str | Path | None = None,
    retain_fixture_artifacts: bool = False,
    operator_id: str = DEFAULT_OPERATOR_ID,
) -> dict[str, Any]:
    """Run anonymized fixture packets through the import preview pipeline."""

    vault = Path(vault_root).resolve()
    run_root, default_cleanup = _safe_run_root(fixture_root)
    cleanup = default_cleanup and not retain_fixture_artifacts
    positive_results: list[dict[str, Any]] = []
    negative_results: list[dict[str, Any]] = []
    cleanup_performed = False
    cleanup_error = ""

    try:
        for fixture in POSITIVE_FIXTURES:
            positive_results.append(_run_positive_fixture(run_root, fixture, operator_id))
        for fixture in NEGATIVE_FIXTURES:
            negative_results.append(_run_negative_fixture(run_root, fixture, operator_id))
    finally:
        if cleanup:
            try:
                shutil.rmtree(run_root, ignore_errors=False)
                cleanup_performed = True
            except OSError as exc:
                cleanup_error = str(exc)

    coverage = _coverage(positive_results)
    positive_pass_count = sum(1 for result in positive_results if result.get("ok"))
    negative_pass_count = sum(1 for result in negative_results if result.get("ok"))
    canonical_violation_count = sum(
        len(result.get("canonical_write_violations") or [])
        for result in positive_results + negative_results
    )
    blocker_reasons = list(
        dict.fromkeys(
            reason
            for result in positive_results + negative_results
            for reason in result.get("blocked_reasons", [])
            if not (result.get("category") == "negative" and reason in result.get("expected_blockers", []))
        )
    )
    ok = (
        positive_pass_count == len(POSITIVE_FIXTURES)
        and negative_pass_count == len(NEGATIVE_FIXTURES)
        and coverage["missing_required_rule_count"] == 0
        and canonical_violation_count == 0
        and not cleanup_error
    )

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if ok else FAILED_STATUS,
        "vault_root": str(vault),
        "source_text_included_in_payload": False,
        "fixture_run": {
            "fixture_run_root": str(run_root),
            "fixture_root_retained": bool(retain_fixture_artifacts or fixture_root is not None),
            "temporary_fixture_root_used": fixture_root is None,
            "temporary_fixture_root_cleanup_requested": cleanup,
            "temporary_fixture_root_cleanup_performed": cleanup_performed,
            "fixture_run_root_exists_after": run_root.exists(),
            "cleanup_error": cleanup_error or None,
        },
        "summary": {
            "positive_fixture_count": len(POSITIVE_FIXTURES),
            "negative_fixture_count": len(NEGATIVE_FIXTURES),
            "fixture_count": len(POSITIVE_FIXTURES) + len(NEGATIVE_FIXTURES),
            "positive_pass_count": positive_pass_count,
            "negative_pass_count": negative_pass_count,
            "execution_success_count": sum(1 for result in positive_results if result.get("execution_ok")),
            "required_rule_coverage_count": coverage["positive_fixture_required_rule_count"],
            "missing_required_rule_id_count": coverage["missing_required_rule_count"],
            "canonical_write_violation_count": canonical_violation_count,
            "secret_blocker_success_count": sum(
                1 for result in negative_results if result.get("expected_blockers_present")
            ),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "fixture_catalog": [_fixture_public(item) for item in POSITIVE_FIXTURES + NEGATIVE_FIXTURES],
        "positive_fixture_results": positive_results,
        "negative_fixture_results": negative_results,
        "coverage": coverage,
        "readiness": {
            "multi_instance_test_harness_built": True,
            "multi_instance_positive_fixtures_passed": positive_pass_count == len(POSITIVE_FIXTURES),
            "multi_instance_negative_fixtures_passed": negative_pass_count == len(NEGATIVE_FIXTURES),
            "positive_required_rule_coverage_passed": coverage["missing_required_rule_count"] == 0,
            "secret_blocking_fixture_passed": negative_pass_count == len(NEGATIVE_FIXTURES),
            "approved_preview_execution_proof_exercised": bool(positive_results),
            "canonical_write_block_verified": canonical_violation_count == 0,
            "source_text_not_returned": True,
            "runtime_consumption_live_verified": False,
            "canonical_promotion_writer_built": True,
            "live_import_writes_enabled": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "authority": {
            "reads_live_vault": False,
            "writes_live_vault": False,
            "writes_fixture_vaults_only": True,
            "fixture_artifact_cleanup_allowed": True,
            "approval_queue_write_allowed_in_fixture_vaults": True,
            "approved_preview_execution_allowed_in_fixture_vaults": True,
            "canonical_mutation_allowed": False,
            "personal_map_apply_allowed": False,
            "runtime_memory_mutation_allowed": False,
            "agent_bus_dispatch_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
        },
        "blocked_reasons": blocker_reasons,
    }
