"""CLI wording regression tests for the approved target upgrade executor."""

from __future__ import annotations

import argparse
from pathlib import Path

import runtime.cli.main as cli


def _subparser_action(parser: argparse.ArgumentParser) -> argparse._SubParsersAction | None:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    return None


def _resolve_parser(path: list[str]) -> argparse.ArgumentParser:
    parser = cli.build_parser()
    for token in path:
        subparser = _subparser_action(parser)
        assert subparser is not None
        parser = subparser.choices[token]
    return parser


def test_approved_target_upgrade_executor_help_matches_approval_scoped_boundary() -> None:
    parser = _resolve_parser(["studio"])
    studio_subparser = _subparser_action(parser)
    assert studio_subparser is not None

    choice_help = next(
        action.help
        for action in studio_subparser._choices_actions
        if action.dest == "approved-target-upgrade-executor"
    )
    formatted_help = parser.format_help()

    # The command must no longer advertise itself as temp-target-only; its contract
    # allows approval-scoped, create-only target writes under separate Gate/review authority.
    assert "approval-scoped create-only target upgrade executor" in choice_help
    assert "approval-scoped" in formatted_help
    assert "create-only target" in formatted_help
    assert "temp-target approved upgrade executor proof" not in choice_help
    assert "temp-target approved upgrade executor proof" not in formatted_help


def test_approved_target_upgrade_executor_text_boundary_matches_contract(tmp_path: Path, capsys) -> None:
    exit_code = cli.main(
        [
            "studio",
            "approved-target-upgrade-executor",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            "missing-approval",
            "--target-path",
            str(tmp_path / "candidate-target"),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Boundary: approval-scoped create-only target writes" in output
    assert "target fingerprint/evidence collision checks" in output
    assert "no operator-selected live target use without separate Gate/review authority" in output
    assert "temp-target proof only" not in output
    assert "no operator live target run" not in output
    assert not (tmp_path / "candidate-target").exists()
