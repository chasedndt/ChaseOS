from __future__ import annotations

from pathlib import Path

from runtime.operator_surface import terminal_runs


def _classification(allowed: bool = True, action_class: str = "read_only_command") -> dict:
    return {"action_class": action_class, "allowed": allowed, "approval_required": not allowed}


def test_new_run_id_shape() -> None:
    rid = terminal_runs.new_run_id()
    assert rid.startswith("term_")
    assert len(rid.split("_")) == 3


def test_build_run_record_fields() -> None:
    record = terminal_runs.build_run_record(
        command="git status", cwd="/repo", classification=_classification(),
        policy_decision="executed", exit_code=0, stdout_excerpt="clean",
    )
    assert record["command"] == "git status"
    assert record["classification"] == "read_only_command"
    assert record["trust_state"] == "Tier 4"
    assert record["terminal_output_trusted"] is False
    assert record["policy_decision"] == "executed"


def test_record_and_list_and_load(tmp_path: Path) -> None:
    record = terminal_runs.build_run_record(
        command="pwd", cwd=str(tmp_path), classification=_classification(),
        policy_decision="executed", exit_code=0, stdout_excerpt="/x",
    )
    paths = terminal_runs.record_terminal_run(tmp_path, record)
    assert Path(paths["json"]).exists()
    assert Path(paths["markdown"]).exists()

    runs = terminal_runs.list_terminal_runs(tmp_path)
    assert len(runs) == 1
    assert runs[0]["run_id"] == record["run_id"]

    loaded = terminal_runs.load_terminal_run(tmp_path, record["run_id"])
    assert loaded is not None
    assert loaded["command"] == "pwd"


def test_markdown_marks_untrusted(tmp_path: Path) -> None:
    record = terminal_runs.build_run_record(
        command="pwd", cwd=str(tmp_path), classification=_classification(),
        policy_decision="executed", stdout_excerpt="data",
    )
    paths = terminal_runs.record_terminal_run(tmp_path, record)
    body = Path(paths["markdown"]).read_text(encoding="utf-8")
    assert "Tier 4" in body
    assert "NOT trusted instruction" in body


def test_list_empty_when_no_root(tmp_path: Path) -> None:
    assert terminal_runs.list_terminal_runs(tmp_path) == []


def test_load_rejects_traversal(tmp_path: Path) -> None:
    assert terminal_runs.load_terminal_run(tmp_path, "../escape") is None


def test_load_terminal_run_detail_returns_full_record(tmp_path: Path) -> None:
    record = terminal_runs.build_run_record(
        command="pwd",
        cwd=str(tmp_path),
        classification=_classification(),
        policy_decision="executed",
        exit_code=0,
        stdout_excerpt="hello",
        duration_ms=12,
    )
    terminal_runs.record_terminal_run(tmp_path, record)

    detail = terminal_runs.load_terminal_run_detail(tmp_path, record["run_id"])

    assert detail["ok"] is True
    assert detail["record"]["run_id"] == record["run_id"]
    assert detail["record"]["stdout_excerpt"] == "hello"
    assert detail["record"]["duration_ms"] == 12
    assert detail["terminal_output_trusted"] is False


def test_load_terminal_run_detail_missing_and_unsafe(tmp_path: Path) -> None:
    missing = terminal_runs.load_terminal_run_detail(tmp_path, "term_missing")
    unsafe = terminal_runs.load_terminal_run_detail(tmp_path, "../escape")

    assert missing["ok"] is False
    assert missing["error"]["code"] == "run_not_found"
    assert unsafe["ok"] is False
    assert unsafe["error"]["code"] == "unsafe_run_id"


def test_blocked_run_is_recorded(tmp_path: Path) -> None:
    record = terminal_runs.build_run_record(
        command="rm -rf /", cwd=str(tmp_path),
        classification=_classification(allowed=False, action_class="destructive_command"),
        policy_decision="blocked",
    )
    paths = terminal_runs.record_terminal_run(tmp_path, record)
    loaded = terminal_runs.load_terminal_run(tmp_path, record["run_id"])
    assert loaded["policy_decision"] == "blocked"
    assert loaded["allowed"] is False
    assert Path(paths["json"]).exists()
