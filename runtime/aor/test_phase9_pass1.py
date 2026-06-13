"""
test_phase9_pass1.py — ChaseOS Phase 9 Pass 1
Tests for the AOR Execution Engine foundation.

Coverage:
  Registry:
  - load_manifest: valid manifest loads and validates correctly
  - load_manifest: missing manifest returns None (not exception)
  - load_manifest: missing required fields raises ValueError
  - load_manifest: id mismatch raises ValueError
  - load_manifest: invalid trigger_type raises ValueError
  - load_manifest: invalid status raises ValueError
  - load_manifest: disabled workflow still loads (status check in engine)
  - list_manifests: returns all valid manifests; skips _schema files
  - list_manifests: empty registry dir returns empty list

  Role Cards:
  - load_card: valid card loads and validates correctly
  - load_card: missing card returns None
  - load_card: missing required fields raises ValueError
  - load_card: id mismatch raises ValueError
  - list_cards: returns all valid cards; skips _schema files

  Task Router:
  - classify: known task type returns correct type dict
  - classify: unknown task type id returns UNCLASSIFIED_SENTINEL
  - classify: "unclassified" explicitly returns UNCLASSIFIED_SENTINEL
  - UNCLASSIFIED_SENTINEL has runtime_class "escalate"
  - list_task_types: returns all non-sentinel types

  Engine — Pipeline Escalation:
  - stage 1: workflow not in registry → escalated at workflow_lookup
  - stage 1: disabled workflow → escalated at workflow_lookup
  - stage 2: bad task_type in manifest → escalated at task_classification
  - stage 3: missing role card → escalated at role_card_resolution
  - stage 4: forbidden write zone in inputs → escalated at permission_ceiling
  - stage 5: required reads not on disk → escalated at required_reads

  Engine — Happy Path:
  - dry_run=True → status="dry_run_ok" after all stages pass
  - operator_today active workflow → status="success" with real handler dispatch
  - run_workflow writes audit record to 07_LOGS/Agent-Activity/

  Integration:
  - operator-briefing role card loads and validates
  - vault-maintenance role card loads and validates
  - operator_today manifest loads and validates
  - operator_close_day manifest loads and validates
  - graph_hygiene manifest loads and validates
  - graduate_ideas manifest loads and validates

Running:
  PYTHONIOENCODING=utf-8 python runtime/aor/test_phase9_pass1.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import uuid
from pathlib import Path

# Ensure vault root is importable
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(errors="replace")

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.registry import load_manifest, list_manifests, _validate_manifest
from runtime.aor.role_cards import load_card, list_cards, _validate_card
from runtime.aor.task_router import classify, list_task_types, UNCLASSIFIED_SENTINEL
from runtime.aor.engine import run_workflow, AORRunResult


# ── Test runner infrastructure ────────────────────────────────────────────────

_TESTS: list[tuple[str, object]] = []
_PASS = 0
_FAIL = 0
_ERRORS: list[str] = []


class _LocalTempVault:
    def __init__(self, root: Path) -> None:
        self.name = str(root)

    def cleanup(self) -> None:
        shutil.rmtree(self.name, ignore_errors=True)


def _test(name: str):
    def decorator(fn):
        _TESTS.append((name, fn))
        return fn
    return decorator


def _run_all() -> None:
    global _PASS, _FAIL
    for name, fn in _TESTS:
        try:
            fn()
            print(f"  PASS  {name}")
            _PASS += 1
        except AssertionError as exc:
            print(f"  FAIL  {name}: {exc}")
            _FAIL += 1
            _ERRORS.append(f"{name}: {exc}")
        except Exception as exc:
            print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
            _FAIL += 1
            _ERRORS.append(f"{name}: {type(exc).__name__}: {exc}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_valid_manifest(workflow_id: str = "test_workflow") -> dict:
    return {
        "id": workflow_id,
        "name": "Test Workflow",
        "version": "1.0",
        "description": "A test workflow for unit testing.",
        "task_type": "operator-briefing",
        "role_card": "operator-briefing",
        "trigger_type": "manual",
        "owner": "operator",
        "status": "active",
        "permission_ceiling": "no_protected_file_writes",
        "writeback_targets": ["07_LOGS/Daily/"],
        "failure_behavior": "escalate",
    }


def _make_valid_card(card_id: str = "test-card") -> dict:
    return {
        "id": card_id,
        "name": "Test Role Card",
        "version": "1.0",
        "description": "A test role card.",
        "owner": "operator",
        "allowed_actions": ["read_vault"],
        "forbidden_actions": ["write_protected_files"],
        "write_scope": ["07_LOGS/Daily/"],
        "forbidden_write_zones": ["SOUL.md", "CLAUDE.md"],
        "escalation_rules": ["write outside scope"],
        "runtime_expectations": ["vault root accessible"],
    }


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if any(ch in text for ch in [":", "#", "[", "]"]) or text.strip() != text or "\n" in text:
        return '"' + text.replace('"', '\\"') + '"'
    return text


def _yaml_dump(data: object, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(data, dict):
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(_yaml_dump(value, indent + 2).rstrip("\n"))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")
        return "\n".join(lines) + "\n"
    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.append(_yaml_dump(item, indent + 2).rstrip("\n"))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return "\n".join(lines) + "\n"
    return f"{prefix}{_yaml_scalar(data)}\n"


def _make_temp_vault() -> _LocalTempVault:
    """Create a minimal temp directory that looks like a vault."""
    tmp_root = _VAULT_ROOT / ".codex_tmp_test"
    tmp_root.mkdir(parents=True, exist_ok=True)
    root = tmp_root / f"aor-pass1-{uuid.uuid4().hex}"
    root.mkdir()
    # Create the marker file
    (root / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
    # Create the required reads path used by operator-briefing role card
    (root / "00_HOME").mkdir()
    (root / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    return _LocalTempVault(root)


def _populate_operator_today_context(root: Path) -> None:
    (root / "03_INPUTS" / "Sources").mkdir(parents=True)
    (root / "07_LOGS" / "Build-Logs").mkdir(parents=True)
    (root / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
    (root / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
    (root / "01_PROJECTS" / "TradingSystems").mkdir(parents=True)
    (root / "01_PROJECTS" / "StrikeZone").mkdir(parents=True)
    (root / "01_PROJECTS" / "University").mkdir(parents=True)

    (root / "00_HOME" / "Now.md").write_text(
        "\n".join(
            [
                "## Current Phase",
                "Phase 9 active.",
                "",
                "## Active Now",
                "| Domain | Current focus |",
                "|--------|---------------|",
                "| ChaseOS / System Infrastructure | Phase 9 Pass 2 |",
                "| Trading Systems / Market Ops | Daily execution |",
                "| StrikeZone Crypto | Community ops |",
                "| University | Coursework |",
                "",
                "- ⬜ Pass 2 (NEXT): Continue Phase 9 handler enablement",
            ]
        ),
        encoding="utf-8",
    )
    (root / "01_PROJECTS" / "ChaseOS" / "ChaseOS-OS.md").write_text(
        "## Open Loops\n- [ ] Keep AOR moving\n",
        encoding="utf-8",
    )
    (root / "01_PROJECTS" / "TradingSystems" / "TradingSystems-OS.md").write_text(
        "## 12. Immediate Next Actions\n- [ ] Formalize scoring\n",
        encoding="utf-8",
    )
    (root / "01_PROJECTS" / "StrikeZone" / "StrikeZone-Crypto-OS.md").write_text(
        "## 🔗 Open Loops\n- [ ] Build testimonial capture system\n",
        encoding="utf-8",
    )
    (root / "01_PROJECTS" / "University" / "Degree-OS.md").write_text(
        "## 🔗 Open Loops\n- [ ] Add deadlines\n",
        encoding="utf-8",
    )
    (root / "07_LOGS" / "Build-Logs" / "2026-04-09-example.md").write_text("build log", encoding="utf-8")
    (root / "07_LOGS" / "Decision-Ledger" / "2026-04-09-example.md").write_text("decision", encoding="utf-8")
    (root / "03_INPUTS" / "Sources" / "20260409-000000__source__test.md").write_text(
        "capture",
        encoding="utf-8",
    )


# ── Registry Tests ─────────────────────────────────────────────────────────────

@_test("registry: valid manifest loads and validates")
def test_registry_valid_manifest():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    data = _make_valid_manifest("my_workflow")
    (reg_dir / "my_workflow.yaml").write_text(_yaml_dump(data))

    result = load_manifest("my_workflow", vault_root=root)
    assert result is not None
    assert result["id"] == "my_workflow"
    assert result["task_type"] == "operator-briefing"
    tmp.cleanup()


@_test("registry: fallback parser works without PyYAML")
def test_registry_fallback_parser_without_pyyaml():
    from unittest.mock import patch
    import runtime.aor.registry as registry_mod

    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    data = _make_valid_manifest("fallback_workflow")
    data["notes"] = "simple fallback path"
    (reg_dir / "fallback_workflow.yaml").write_text(_yaml_dump(data), encoding="utf-8")

    with patch.object(registry_mod, "yaml", None):
        result = load_manifest("fallback_workflow", vault_root=root)
    assert result is not None
    assert result["id"] == "fallback_workflow"
    assert result["task_type"] == "operator-briefing"
    tmp.cleanup()


@_test("registry: fallback parser preserves empty inline lists")
def test_registry_fallback_parser_preserves_empty_inline_lists():
    from unittest.mock import patch
    import runtime.aor.registry as registry_mod

    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    data = _make_valid_manifest("fallback_empty_list_workflow")
    data["required_reads"] = []
    text = _yaml_dump(data).replace("required_reads:\n", "required_reads: []\n")
    (reg_dir / "fallback_empty_list_workflow.yaml").write_text(text, encoding="utf-8")

    with patch.object(registry_mod, "yaml", None):
        result = load_manifest("fallback_empty_list_workflow", vault_root=root)
    assert result is not None
    assert result["required_reads"] == []
    tmp.cleanup()


@_test("registry: missing manifest returns None")
def test_registry_missing_returns_none():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    (root / "runtime" / "workflows" / "registry").mkdir(parents=True)

    result = load_manifest("nonexistent_workflow", vault_root=root)
    assert result is None
    tmp.cleanup()


@_test("registry: missing required fields raises ValueError")
def test_registry_missing_fields():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    # Missing most required fields
    data = {"id": "bad_workflow", "name": "Bad"}
    (reg_dir / "bad_workflow.yaml").write_text(_yaml_dump(data))

    try:
        load_manifest("bad_workflow", vault_root=root)
        assert False, "should have raised ValueError"
    except ValueError as exc:
        assert "missing required fields" in str(exc)
    tmp.cleanup()


@_test("registry: id mismatch raises ValueError")
def test_registry_id_mismatch():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    data = _make_valid_manifest("different_id")
    # File is named mismatch_workflow.yaml but id says different_id
    (reg_dir / "mismatch_workflow.yaml").write_text(_yaml_dump(data))

    try:
        load_manifest("mismatch_workflow", vault_root=root)
        assert False, "should have raised ValueError"
    except ValueError as exc:
        assert "must match filename stem" in str(exc)
    tmp.cleanup()


@_test("registry: invalid trigger_type raises ValueError")
def test_registry_invalid_trigger():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    data = _make_valid_manifest("bad_trigger")
    data["trigger_type"] = "autonomous"  # not a valid value
    (reg_dir / "bad_trigger.yaml").write_text(_yaml_dump(data))

    try:
        load_manifest("bad_trigger", vault_root=root)
        assert False, "should have raised ValueError"
    except ValueError as exc:
        assert "trigger_type" in str(exc)
    tmp.cleanup()


@_test("registry: invalid status raises ValueError")
def test_registry_invalid_status():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    data = _make_valid_manifest("bad_status")
    data["status"] = "running"  # not valid
    (reg_dir / "bad_status.yaml").write_text(_yaml_dump(data))

    try:
        load_manifest("bad_status", vault_root=root)
        assert False, "should have raised ValueError"
    except ValueError as exc:
        assert "status" in str(exc)
    tmp.cleanup()


@_test("registry: disabled workflow loads (engine handles status check)")
def test_registry_disabled_loads():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    data = _make_valid_manifest("disabled_wf")
    data["status"] = "disabled"
    (reg_dir / "disabled_wf.yaml").write_text(_yaml_dump(data))

    result = load_manifest("disabled_wf", vault_root=root)
    assert result is not None
    assert result["status"] == "disabled"
    tmp.cleanup()


@_test("registry: list_manifests returns valid manifests; skips _schema files")
def test_registry_list_manifests():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    # Valid manifest
    data_a = _make_valid_manifest("workflow_a")
    (reg_dir / "workflow_a.yaml").write_text(_yaml_dump(data_a))
    data_b = _make_valid_manifest("workflow_b")
    (reg_dir / "workflow_b.yaml").write_text(_yaml_dump(data_b))
    # Schema file — should be skipped
    (reg_dir / "_schema.yaml").write_text("# schema")

    results = list_manifests(vault_root=root)
    ids = [r["id"] for r in results]
    assert "workflow_a" in ids
    assert "workflow_b" in ids
    assert len(results) == 2  # _schema not included
    tmp.cleanup()


@_test("registry: list_manifests on empty dir returns empty list")
def test_registry_list_empty():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    # No registry dir created
    results = list_manifests(vault_root=root)
    assert results == []
    tmp.cleanup()


# ── Role Card Tests ────────────────────────────────────────────────────────────

@_test("role_cards: valid card loads and validates")
def test_card_valid():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    cards_dir = root / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)
    data = _make_valid_card("my-card")
    (cards_dir / "my-card.yaml").write_text(_yaml_dump(data))

    result = load_card("my-card", vault_root=root)
    assert result is not None
    assert result["id"] == "my-card"
    tmp.cleanup()


@_test("role_cards: fallback parser works without PyYAML")
def test_card_fallback_parser_without_pyyaml():
    from unittest.mock import patch
    import runtime.aor.role_cards as role_cards_mod

    tmp = _make_temp_vault()
    root = Path(tmp.name)
    cards_dir = root / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)
    data = _make_valid_card("fallback-card")
    (cards_dir / "fallback-card.yaml").write_text(_yaml_dump(data), encoding="utf-8")

    with patch.object(role_cards_mod, "yaml", None):
        result = load_card("fallback-card", vault_root=root)
    assert result is not None
    assert result["id"] == "fallback-card"
    assert result["allowed_actions"] == ["read_vault"]
    tmp.cleanup()


@_test("role_cards: fallback parser preserves empty inline lists")
def test_card_fallback_parser_preserves_empty_inline_lists():
    from unittest.mock import patch
    import runtime.aor.role_cards as role_cards_mod

    tmp = _make_temp_vault()
    root = Path(tmp.name)
    cards_dir = root / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)
    data = _make_valid_card("fallback-empty-list-card")
    data["required_reads"] = []
    text = _yaml_dump(data).replace("required_reads:\n", "required_reads: []\n")
    (cards_dir / "fallback-empty-list-card.yaml").write_text(text, encoding="utf-8")

    with patch.object(role_cards_mod, "yaml", None):
        result = load_card("fallback-empty-list-card", vault_root=root)
    assert result is not None
    assert result["required_reads"] == []
    tmp.cleanup()


@_test("role_cards: missing card returns None")
def test_card_missing():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    (root / "06_AGENTS" / "role-cards").mkdir(parents=True)

    result = load_card("nonexistent-card", vault_root=root)
    assert result is None
    tmp.cleanup()


@_test("role_cards: missing required fields raises ValueError")
def test_card_missing_fields():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    cards_dir = root / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)
    data = {"id": "bad-card", "name": "Bad"}
    (cards_dir / "bad-card.yaml").write_text(_yaml_dump(data))

    try:
        load_card("bad-card", vault_root=root)
        assert False, "should have raised ValueError"
    except ValueError as exc:
        assert "missing required fields" in str(exc)
    tmp.cleanup()


@_test("role_cards: id mismatch raises ValueError")
def test_card_id_mismatch():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    cards_dir = root / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)
    data = _make_valid_card("wrong-id")
    (cards_dir / "actual-name.yaml").write_text(_yaml_dump(data))

    try:
        load_card("actual-name", vault_root=root)
        assert False, "should have raised ValueError"
    except ValueError as exc:
        assert "must match filename stem" in str(exc)
    tmp.cleanup()


@_test("role_cards: list_cards skips _schema files")
def test_card_list_skips_schema():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    cards_dir = root / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)
    data = _make_valid_card("real-card")
    (cards_dir / "real-card.yaml").write_text(_yaml_dump(data))
    (cards_dir / "_schema.yaml").write_text("# schema")

    results = list_cards(vault_root=root)
    assert len(results) == 1
    assert results[0]["id"] == "real-card"
    tmp.cleanup()


# ── Task Router Tests ──────────────────────────────────────────────────────────

@_test("task_router: known task type returns correct definition")
def test_router_known_type():
    result = classify("operator-briefing")
    assert result["id"] == "operator-briefing"
    assert result["runtime_class"] == "read-heavy"
    assert result["id"] != "unclassified"


@_test("task_router: unknown task type returns UNCLASSIFIED_SENTINEL")
def test_router_unknown_type():
    result = classify("completely-made-up-type-xyz")
    assert result["id"] == "unclassified"
    assert result["runtime_class"] == "escalate"


@_test("task_router: 'unclassified' id explicitly returns sentinel")
def test_router_explicit_unclassified():
    result = classify("unclassified")
    assert result is UNCLASSIFIED_SENTINEL or result["id"] == "unclassified"


@_test("task_router: UNCLASSIFIED_SENTINEL has runtime_class escalate")
def test_router_sentinel_runtime_class():
    assert UNCLASSIFIED_SENTINEL["runtime_class"] == "escalate"
    assert "always" in UNCLASSIFIED_SENTINEL["escalation_trigger"][0].lower()


@_test("task_router: list_task_types returns non-empty list without sentinel")
def test_router_list_types():
    types = list_task_types()
    assert len(types) > 0
    ids = [t["id"] for t in types]
    assert "unclassified" not in ids
    assert "operator-briefing" in ids


@_test("task_router: fallback parser preserves empty inline required_reads")
def test_router_fallback_parser_preserves_empty_inline_required_reads():
    from unittest.mock import patch
    import runtime.aor.task_router as task_router_mod

    with patch.object(task_router_mod, "yaml", None):
        result = classify("source-pack-builder")

    assert result["id"] == "source-pack-builder"
    assert result["required_reads"] == []


# ── Engine — Escalation Tests ──────────────────────────────────────────────────

@_test("engine: workflow not in registry → escalated at workflow_lookup")
def test_engine_not_in_registry():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    (root / "runtime" / "workflows" / "registry").mkdir(parents=True)
    (root / "06_AGENTS" / "role-cards").mkdir(parents=True)

    result = run_workflow("nonexistent_workflow", vault_root=root)
    assert result.status == "escalated"
    assert result.stage_reached == "workflow_lookup"
    assert "not found in registry" in (result.escalation_reason or "")
    tmp.cleanup()


@_test("engine: disabled workflow → escalated at workflow_lookup")
def test_engine_disabled_workflow():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    (root / "06_AGENTS" / "role-cards").mkdir(parents=True)

    data = _make_valid_manifest("disabled_wf")
    data["status"] = "disabled"
    (reg_dir / "disabled_wf.yaml").write_text(_yaml_dump(data))

    result = run_workflow("disabled_wf", vault_root=root)
    assert result.status == "escalated"
    assert result.stage_reached == "workflow_lookup"
    assert "not runnable" in (result.escalation_reason or "")
    tmp.cleanup()


@_test("engine: draft workflow → escalated at workflow_lookup")
def test_engine_draft_workflow():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)

    data = _make_valid_manifest("draft_wf")
    data["status"] = "draft"
    (reg_dir / "draft_wf.yaml").write_text(_yaml_dump(data))

    result = run_workflow("draft_wf", vault_root=root)
    assert result.status == "escalated"
    assert result.stage_reached == "workflow_lookup"
    assert "status='active'" in (result.escalation_reason or "")
    tmp.cleanup()


@_test("engine: bad task_type in manifest → escalated at task_classification")
def test_engine_bad_task_type():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    (root / "06_AGENTS" / "role-cards").mkdir(parents=True)

    data = _make_valid_manifest("wf_bad_type")
    data["task_type"] = "definitely-not-a-real-task-type"
    (reg_dir / "wf_bad_type.yaml").write_text(_yaml_dump(data))

    result = run_workflow("wf_bad_type", vault_root=root)
    assert result.status == "escalated"
    assert result.stage_reached == "task_classification"
    assert "not in the task type table" in (result.escalation_reason or "")
    tmp.cleanup()


@_test("engine: missing role card → escalated at role_card_resolution")
def test_engine_missing_role_card():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    (root / "06_AGENTS" / "role-cards").mkdir(parents=True)

    data = _make_valid_manifest("wf_no_card")
    data["role_card"] = "nonexistent-card"
    (reg_dir / "wf_no_card.yaml").write_text(_yaml_dump(data))

    result = run_workflow("wf_no_card", vault_root=root)
    assert result.status == "escalated"
    assert result.stage_reached == "role_card_resolution"
    assert "not found" in (result.escalation_reason or "")
    tmp.cleanup()


@_test("engine: forbidden write zone in inputs → escalated at permission_ceiling")
def test_engine_forbidden_write_zone():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    cards_dir = root / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)

    data = _make_valid_manifest("wf_ceiling")
    (reg_dir / "wf_ceiling.yaml").write_text(_yaml_dump(data))
    card_data = _make_valid_card("operator-briefing")
    card_data["forbidden_write_zones"] = ["SOUL.md", "CLAUDE.md"]
    (cards_dir / "operator-briefing.yaml").write_text(_yaml_dump(card_data))

    # Pass a write_path that hits a forbidden zone
    result = run_workflow("wf_ceiling", inputs={"write_path": "SOUL.md"}, vault_root=root)
    assert result.status == "escalated"
    assert result.stage_reached == "permission_ceiling"
    assert "forbidden write zone" in (result.escalation_reason or "")
    tmp.cleanup()


@_test("engine: required read not on disk → escalated at required_reads")
def test_engine_required_reads_missing():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    cards_dir = root / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)

    data = _make_valid_manifest("wf_reads")
    (reg_dir / "wf_reads.yaml").write_text(_yaml_dump(data))

    card_data = _make_valid_card("operator-briefing")
    # Point required_reads at a path that definitely doesn't exist
    card_data["required_reads"] = ["this/path/does/not/exist.md"]
    (cards_dir / "operator-briefing.yaml").write_text(_yaml_dump(card_data))

    result = run_workflow("wf_reads", vault_root=root)
    assert result.status == "escalated"
    assert result.stage_reached == "required_reads"
    assert "required reads not accessible" in (result.escalation_reason or "")
    tmp.cleanup()


# ── Engine — Happy Path Tests ──────────────────────────────────────────────────

@_test("engine: dry_run=True → status=dry_run_ok when all stages pass")
def test_engine_dry_run():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    cards_dir = root / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)
    (root / "03_INPUTS").mkdir()
    (root / "07_LOGS" / "Build-Logs").mkdir(parents=True)
    (root / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)

    data = _make_valid_manifest("wf_dry")
    (reg_dir / "wf_dry.yaml").write_text(_yaml_dump(data))

    card_data = _make_valid_card("operator-briefing")
    card_data["required_reads"] = [
        "00_HOME/Now.md",
        "03_INPUTS/",
        "07_LOGS/Build-Logs/",
        "07_LOGS/Decision-Ledger/",
    ]
    (cards_dir / "operator-briefing.yaml").write_text(_yaml_dump(card_data))

    result = run_workflow("wf_dry", vault_root=root, dry_run=True)
    assert result.status == "dry_run_ok"
    assert result.stage_reached == "dry_run_exit"
    assert result.outputs.get("dry_run") is True
    tmp.cleanup()


@_test("engine: operator_today active workflow → status=success with real handler dispatch")
def test_engine_success_operator_today():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    cards_dir = root / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)
    _populate_operator_today_context(root)

    data = _make_valid_manifest("operator_today")
    data["writeback_targets"] = ["07_LOGS/Operator-Briefs/"]
    (reg_dir / "operator_today.yaml").write_text(_yaml_dump(data))

    card_data = _make_valid_card("operator-briefing")
    card_data["write_scope"] = ["07_LOGS/Operator-Briefs/", "07_LOGS/Agent-Activity/"]
    card_data["required_reads"] = [
        "00_HOME/Now.md",
        "03_INPUTS/",
        "07_LOGS/Build-Logs/",
        "07_LOGS/Decision-Ledger/",
    ]
    (cards_dir / "operator-briefing.yaml").write_text(_yaml_dump(card_data))

    result = run_workflow("operator_today", inputs={"date": "2026-04-09"}, vault_root=root)
    assert result.status == "success"
    assert result.outputs["run"]["handler_status"] == "executed"
    assert result.outputs["writeback"]["files_written"] == [
        "07_LOGS/Operator-Briefs/2026-04-09-operator-today.md"
    ]
    tmp.cleanup()


@_test("engine: run_workflow writes audit record to 07_LOGS/Agent-Activity/")
def test_engine_audit_record_written():
    tmp = _make_temp_vault()
    root = Path(tmp.name)
    reg_dir = root / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)
    cards_dir = root / "06_AGENTS" / "role-cards"
    cards_dir.mkdir(parents=True)
    _populate_operator_today_context(root)

    data = _make_valid_manifest("operator_today")
    data["writeback_targets"] = ["07_LOGS/Operator-Briefs/"]
    (reg_dir / "operator_today.yaml").write_text(_yaml_dump(data))
    card_data = _make_valid_card("operator-briefing")
    card_data["write_scope"] = ["07_LOGS/Operator-Briefs/", "07_LOGS/Agent-Activity/"]
    card_data["required_reads"] = [
        "00_HOME/Now.md",
        "03_INPUTS/",
        "07_LOGS/Build-Logs/",
        "07_LOGS/Decision-Ledger/",
    ]
    (cards_dir / "operator-briefing.yaml").write_text(_yaml_dump(card_data))

    result = run_workflow("operator_today", inputs={"date": "2026-04-09"}, vault_root=root)
    assert result.status == "success"

    audit_dir = root / "07_LOGS" / "Agent-Activity"
    audit_files = list(audit_dir.glob("*.json"))
    assert len(audit_files) == 1

    with audit_files[0].open() as f:
        record = json.load(f)
    assert record["workflow_id"] == "operator_today"
    assert record["status"] == "success"
    assert record["audit_id"] == result.audit_id
    tmp.cleanup()


# ── Integration Tests — Live Vault Files ──────────────────────────────────────

@_test("integration: operator-briefing role card loads and validates")
def test_integration_card_operator_briefing():
    result = load_card("operator-briefing", vault_root=_VAULT_ROOT)
    assert result is not None
    assert result["id"] == "operator-briefing"
    assert "read_any_non_protected_file" in result["allowed_actions"]
    assert "write_protected_files" in result["forbidden_actions"]
    assert "SOUL.md" in result["forbidden_write_zones"]


@_test("integration: vault-maintenance role card loads and validates")
def test_integration_card_vault_maintenance():
    result = load_card("vault-maintenance", vault_root=_VAULT_ROOT)
    assert result is not None
    assert result["id"] == "vault-maintenance"
    assert "delete_any_file" in result["forbidden_actions"]
    assert "07_LOGS/Hygiene-Reports/" in result["write_scope"]


@_test("integration: operator_today manifest loads and validates")
def test_integration_manifest_operator_today():
    result = load_manifest("operator_today", vault_root=_VAULT_ROOT)
    assert result is not None
    assert result["id"] == "operator_today"
    assert result["task_type"] == "operator-briefing"
    assert result["role_card"] == "operator-briefing"
    assert result["status"] == "active"


@_test("integration: operator_close_day manifest loads and validates")
def test_integration_manifest_operator_close_day():
    result = load_manifest("operator_close_day", vault_root=_VAULT_ROOT)
    assert result is not None
    assert result["id"] == "operator_close_day"
    assert result["task_type"] == "operator-briefing"


@_test("integration: graph_hygiene manifest loads and validates")
def test_integration_manifest_graph_hygiene():
    result = load_manifest("graph_hygiene", vault_root=_VAULT_ROOT)
    assert result is not None
    assert result["id"] == "graph_hygiene"
    assert result["task_type"] == "graph-hygiene"
    assert result["role_card"] == "vault-maintenance"


@_test("integration: graduate_ideas manifest loads and validates")
def test_integration_manifest_graduate_ideas():
    result = load_manifest("graduate_ideas", vault_root=_VAULT_ROOT)
    assert result is not None
    assert result["id"] == "graduate_ideas"
    assert result["task_type"] == "idea-graduation"


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\nPhase 9 Pass 1 — AOR Foundation Tests")
    print("=" * 60)
    _run_all()
    total = _PASS + _FAIL
    print("=" * 60)
    print(f"Result: {_PASS}/{total} passed")
    if _ERRORS:
        print("\nFailures:")
        for err in _ERRORS:
            print(f"  - {err}")
    sys.exit(0 if _FAIL == 0 else 1)
