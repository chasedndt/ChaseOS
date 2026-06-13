"""Focused tests for Layer C/D memory inspection."""

from __future__ import annotations

import json
import shutil
import sys
import contextlib
import io
from pathlib import Path

try:
    import pytest
except ModuleNotFoundError:  # pragma: no cover - direct script mode without pytest installed
    pytest = None  # type: ignore[assignment]

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import runtime.cli.main as cli  # noqa: E402
from runtime.memory.inspector import (  # noqa: E402
    build_generated_artifact_readiness,
    build_memory_file_structure,
    build_memory_status,
    build_memory_summary,
    get_runtime_memory,
    list_runtime_memory,
    list_task_contexts,
    load_identity_ledger,
    load_task_context,
    validate_memory_substrate,
)


_TESTS: list[tuple[str, object]] = []


def _register(label: str):
    def decorator(fn):
        _TESTS.append((label, fn))
        return fn
    return decorator


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _make_vault(root: Path) -> Path:
    vault = root / "vault"
    vault.mkdir()
    (vault / "CLAUDE.md").write_text("# test", encoding="utf-8")
    return vault


if pytest is not None:
    @pytest.fixture
    def tmp_root(tmp_path: Path) -> Path:
        return tmp_path


@_register("list_runtime_memory merges profile/nav/scorecard/repair stores")
def test_list_runtime_memory(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    _write_json(vault / "runtime/memory/adapters/openclaw/profile.json", {"runtime_id": "openclaw"})
    _write_json(vault / "runtime/memory/adapters/claude/identity-ledger.json", {"runtime_id": "claude"})
    _write_json(vault / "runtime/memory/nav/hermes/nav-map.json", {"runtime_id": "hermes"})
    _write_json(vault / "runtime/memory/repair/openclaw.json", {"runtime_id": "openclaw"})
    _write_json(vault / "runtime/memory/scorecards/hermes.json", {"runtime_id": "hermes"})

    result = list_runtime_memory(vault)
    ids = {item["runtime_id"] for item in result}
    assert ids == {"openclaw", "hermes", "claude"}
    openclaw = next(item for item in result if item["runtime_id"] == "openclaw")
    assert openclaw["profile_present"] is True
    assert openclaw["repair_memory_present"] is True
    claude = next(item for item in result if item["runtime_id"] == "claude")
    assert claude["identity_ledger_present"] is True
    assert claude["profile_present"] is False


@_register("get_runtime_memory returns Layer C and Layer D bundle")
def test_get_runtime_memory(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    _write_json(
        vault / "runtime/memory/adapters/openclaw/profile.json",
        {"runtime_id": "openclaw", "layer": "C", "behavioral_profile": {"primary_role": "test"}},
    )
    _write_json(
        vault / "runtime/memory/adapters/openclaw/identity-ledger.json",
        {
            "schema_version": "1.0",
            "layer": "C",
            "memory_family": "agent_identity_ledger",
            "runtime_id": "openclaw",
            "status": "seeded",
            "identity_summary": {"current_actor_posture": "test identity"},
            "governance_boundary": "identity is advisory evidence and not authority",
        },
    )
    _write_json(
        vault / "runtime/tasks/active/task-1.json",
        {
            "task_id": "task-1",
            "layer": "D",
            "runtime_id": "openclaw",
            "status": "active",
            "objective": "test task",
            "created_at": "2026-04-27T00:00:00Z",
            "memory_boundary": "task-local only",
        },
    )

    bundle = get_runtime_memory("openclaw", vault)
    assert bundle["runtime_id"] == "openclaw"
    assert bundle["layer_c"]["profile"]["behavioral_profile"]["primary_role"] == "test"
    assert bundle["layer_c"]["identity_ledger"]["identity_summary"]["current_actor_posture"] == "test identity"
    assert len(bundle["layer_d"]["active_task_contexts"]) == 1
    assert "cannot override" in bundle["boundaries"]["authority"]


@_register("identity ledger loads as advisory Layer C memory")
def test_load_identity_ledger(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    _write_json(
        vault / "runtime/memory/adapters/hermes/identity-ledger.json",
        {
            "schema_version": "1.0",
            "layer": "C",
            "memory_family": "agent_identity_ledger",
            "runtime_id": "hermes",
            "status": "seeded",
            "identity_summary": {"current_actor_posture": "bounded coordination runtime"},
            "governance_boundary": "identity is advisory evidence and not authority",
        },
    )

    ledger = load_identity_ledger("hermes", vault)
    assert ledger["memory_family"] == "agent_identity_ledger"
    assert ledger["identity_summary"]["current_actor_posture"] == "bounded coordination runtime"
    assert "not authority" in ledger["governance_boundary"]
    missing = load_identity_ledger("openclaw", vault)
    assert missing["status"] == "missing"
    assert missing["memory_family"] == "agent_identity_ledger"


@_register("task context list and load are bounded to active contexts")
def test_task_contexts(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    _write_json(
        vault / "runtime/tasks/active/task-abc.json",
        {
            "task_id": "task-abc",
            "layer": "D",
            "runtime_id": "hermes",
            "status": "active",
            "objective": "coordinate",
            "created_at": "2026-04-27T00:00:00Z",
            "memory_boundary": "task-local only",
        },
    )

    contexts = list_task_contexts(vault)
    assert len(contexts) == 1
    assert contexts[0]["task_id"] == "task-abc"
    loaded = load_task_context("task-abc", vault)
    assert loaded is not None
    assert loaded["runtime_id"] == "hermes"
    assert load_task_context("missing", vault) is None


@_register("validate_memory_substrate reports invalid JSON")
def test_validate_memory_substrate(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    bad = vault / "runtime/memory/repair/bad.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("[1, 2, 3]", encoding="utf-8")

    result = validate_memory_substrate(vault)
    assert result["valid"] is False
    assert result["error_count"] == 1
    assert result["errors"][0]["path"] == "runtime\\memory\\repair\\bad.json" or result["errors"][0]["path"] == "runtime/memory/repair/bad.json"


@_register("build_memory_status returns compact Layer C/D status")
def test_build_memory_status(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    _write_json(vault / "runtime/memory/adapters/openclaw/profile.json", {"runtime_id": "openclaw"})
    status = build_memory_status(vault)
    assert status["layer_c"]["runtime_count"] == 1
    assert status["layer_d"]["active_task_context_count"] == 0


@_register("build_memory_summary consolidates validation coverage and boundaries")
def test_build_memory_summary(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    _write_json(vault / "runtime/memory/adapters/openclaw/profile.json", {"runtime_id": "openclaw"})
    _write_json(
        vault / "runtime/memory/adapters/openclaw/identity-ledger.json",
        {
            "schema_version": "1.0",
            "layer": "C",
            "memory_family": "agent_identity_ledger",
            "runtime_id": "openclaw",
            "status": "seeded",
            "updated_at": "2026-06-12T00:00:00Z",
            "identity_summary": {"current_actor_posture": "test"},
            "behavioral_tendencies": [],
            "doctrine_adherence": {},
            "correction_history": [],
            "drift_signals": [],
            "governance_boundary": "identity is advisory evidence and not authority",
        },
    )
    _write_json(vault / "runtime/memory/nav/openclaw/nav-map.json", {"runtime_id": "openclaw"})
    _write_json(vault / "runtime/memory/repair/openclaw.json", {"runtime_id": "openclaw"})
    _write_json(vault / "runtime/memory/scorecards/openclaw.json", {"runtime_id": "openclaw"})

    summary = build_memory_summary(vault)

    assert summary["read_only"] is True
    assert summary["mutates_memory"] is False
    assert summary["authority_expansion"] is False
    assert summary["memory_posture"] == "ready"
    assert summary["validation"]["valid"] is True
    assert summary["runtime_summary"]["runtime_count"] == 1
    assert summary["runtime_summary"]["runtime_coverage"][0]["complete"] is True
    assert summary["governance"]["memory_overrides_gate"] is False
    assert summary["governance"]["repair_memory_applies_automatically"] is False


@_register("build_memory_summary blocks invalid memory JSON")
def test_build_memory_summary_blocks_invalid_json(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    bad = vault / "runtime/memory/repair/openclaw.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("[1, 2, 3]", encoding="utf-8")

    summary = build_memory_summary(vault)

    assert summary["memory_posture"] == "blocked"
    assert summary["validation"]["valid"] is False
    codes = {item["code"] for item in summary["attention_items"]}
    assert "invalid_memory_json" in codes


@_register("CLI memory summary emits JSON envelope")
def test_cli_memory_summary_json(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    _write_json(vault / "runtime/memory/adapters/openclaw/profile.json", {"runtime_id": "openclaw"})
    _write_json(
        vault / "runtime/memory/adapters/openclaw/identity-ledger.json",
        {
            "schema_version": "1.0",
            "layer": "C",
            "memory_family": "agent_identity_ledger",
            "runtime_id": "openclaw",
            "status": "seeded",
            "updated_at": "2026-06-12T00:00:00Z",
            "identity_summary": {"current_actor_posture": "test"},
            "behavioral_tendencies": [],
            "doctrine_adherence": {},
            "correction_history": [],
            "drift_signals": [],
            "governance_boundary": "identity is advisory evidence and not authority",
        },
    )
    _write_json(vault / "runtime/memory/nav/openclaw/nav-map.json", {"runtime_id": "openclaw"})
    _write_json(vault / "runtime/memory/repair/openclaw.json", {"runtime_id": "openclaw"})
    _write_json(vault / "runtime/memory/scorecards/openclaw.json", {"runtime_id": "openclaw"})

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = cli.main(["memory", "summary", "--vault-root", str(vault), "--json"])

    payload = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "memory.summary"
    assert payload["result"]["memory_posture"] == "ready"
    assert payload["result"]["governance"]["memory_overrides_gate"] is False


@_register("build_memory_file_structure exposes NB-006 read-only path contract")
def test_build_memory_file_structure(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    for rel_path in [
        "runtime/memory/adapters",
        "runtime/memory/nav",
        "runtime/memory/repair",
        "runtime/memory/scorecards",
        "runtime/tasks/active",
        "runtime/tasks/archive",
    ]:
        (vault / rel_path).mkdir(parents=True, exist_ok=True)
    for rel_path in [
        "runtime/memory/README.md",
        "runtime/memory/adapters/_identity_ledger_schema.json",
        "runtime/memory/nav/_schema.json",
        "runtime/memory/repair/_schema.json",
    ]:
        path = vault / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}" if rel_path.endswith(".json") else "# Memory", encoding="utf-8")

    structure = build_memory_file_structure(vault)

    assert structure["source_backlog_id"] == "NB-006"
    assert structure["status"] == "ready"
    assert structure["read_only"] is True
    assert structure["mutates_memory"] is False
    assert structure["missing_paths"] == []
    assert structure["product_surfaces"] == ["Memory Manager", "Memory Ledger", "Context Import"]
    assert structure["governance"]["canonical_promotion_allowed_from_this_surface"] is False
    assert structure["blocked_lower_authority_lane"]["owner_surface"] == "governed Memory Manager / Context Import apply flow"


@_register("CLI memory structure emits NB-006 JSON envelope")
def test_cli_memory_structure_json(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    for rel_path in [
        "runtime/memory/adapters",
        "runtime/memory/nav",
        "runtime/memory/repair",
        "runtime/memory/scorecards",
        "runtime/tasks/active",
        "runtime/tasks/archive",
    ]:
        (vault / rel_path).mkdir(parents=True, exist_ok=True)
    for rel_path in [
        "runtime/memory/README.md",
        "runtime/memory/adapters/_identity_ledger_schema.json",
        "runtime/memory/nav/_schema.json",
        "runtime/memory/repair/_schema.json",
    ]:
        path = vault / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}" if rel_path.endswith(".json") else "# Memory", encoding="utf-8")

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = cli.main(["memory", "structure", "--vault-root", str(vault), "--json"])

    payload = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "memory.structure"
    assert payload["result"]["source_backlog_id"] == "NB-006"
    assert payload["result"]["status"] == "ready"
    assert payload["result"]["missing_paths"] == []


@_register("generated artifact readiness separates workspace candidates from durable Layer C artifacts")
def test_generated_artifact_readiness(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    _write_json(
        vault / "runtime/source_intelligence/workspaces/market-brief/workspace.json",
        {
            "workspace_id": "market-brief",
            "domain": "Trading-Systems",
            "outputs": [
                {
                    "output_id": "out-1",
                    "output_type": "idea_generation_draft",
                    "status": "intermediate",
                    "promotion_candidate": True,
                    "suggested_knowledge_class": "generated-ideas",
                    "promoted_path": None,
                }
            ],
        },
    )
    _write_json(
        vault / "runtime/source_intelligence/workspaces/market-brief/outputs/out-1.json",
        {
            "output_id": "out-1",
            "workspace_id": "market-brief",
            "output_type": "idea_generation_draft",
            "status": "intermediate",
            "promotion_candidate": True,
            "suggested_knowledge_class": "generated-ideas",
            "promoted_path": None,
            "generated_text": "candidate body",
        },
    )
    durable = vault / "02_KNOWLEDGE/Trading-Systems/Generated-Ideas/2026-06-12__synthesis-draft__sample.md"
    durable.parent.mkdir(parents=True, exist_ok=True)
    durable.write_text(
        "---\nknowledge_class: generated-ideas\nendorsement_status: candidate\n---\n# Sample\n",
        encoding="utf-8",
    )

    readiness = build_generated_artifact_readiness(vault)

    assert readiness["read_only"] is True
    assert readiness["mutates_vault"] is False
    assert readiness["creates_generated_ideas_directories"] is False
    assert readiness["gate_required_for_promotion"] is True
    assert readiness["workspace_candidate_count"] == 1
    assert readiness["durable_artifact_count"] == 1
    assert readiness["status"] == "durable-artifacts-present"
    assert readiness["workspace_candidates"][0]["workspace_id"] == "market-brief"
    assert readiness["durable_artifacts"][0]["knowledge_class"] == "generated-ideas"


@_register("CLI memory generated-artifacts emits read-only readiness envelope")
def test_cli_memory_generated_artifacts_json(tmp_root: Path) -> None:
    vault = _make_vault(tmp_root)
    _write_json(
        vault / "runtime/source_intelligence/workspaces/market-brief/workspace.json",
        {
            "workspace_id": "market-brief",
            "domain": "Trading-Systems",
            "outputs": [
                {
                    "output_id": "out-1",
                    "output_type": "idea_generation_draft",
                    "status": "intermediate",
                    "promotion_candidate": True,
                    "suggested_knowledge_class": "generated-ideas",
                }
            ],
        },
    )

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = cli.main(["memory", "generated-artifacts", "--vault-root", str(vault), "--json"])

    payload = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "memory.generated-artifacts"
    assert payload["result"]["workspace_candidate_count"] == 1
    assert payload["result"]["blocked_actions"] == [
        "no Layer C file or directory creation without explicit Gate promotion",
        "no canonical promotion or endorsement status mutation from this status surface",
    ]


def _run_all() -> int:
    print()
    print("=" * 60)
    print("Layer C/D Memory Inspector Tests")
    print("=" * 60)

    failures = 0
    tmp_root = (Path(__file__).resolve().parent / "_tmp_tests").resolve()
    expected_parent = Path(__file__).resolve().parent.resolve()
    if tmp_root.parent != expected_parent:
        raise RuntimeError(f"Refusing unsafe test temp root: {tmp_root}")
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir()

    for index, (label, fn) in enumerate(_TESTS, start=1):
        case_root = tmp_root / f"case_{index:02d}"
        case_root.mkdir()
        try:
            fn(case_root)
            print(f"  PASS  {label}")
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL  {label}")
            print(f"        {type(exc).__name__}: {exc}")
            failures += 1

    if tmp_root.exists():
        shutil.rmtree(tmp_root)

    print()
    total = len(_TESTS)
    passed = total - failures
    print(f"Results: {passed}/{total} passed")
    print("=" * 60)
    print()
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())
