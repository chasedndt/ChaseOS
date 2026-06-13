from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import pytest


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402
from runtime.browser_skills.candidates import (  # noqa: E402
    BrowserSkillCandidateError,
    list_candidate_records,
    preflight_candidate_promotion,
    show_candidate_record,
    storage_reconciliation,
)
from runtime.siteops.candidate_promotions import (  # noqa: E402
    candidate_promotion_apply_contract,
    request_scoped_candidate_promotion,
)

_FIXTURE_ROOT = _VAULT_ROOT / "runtime" / "tests" / "fixtures" / "browser_skill_candidates_vault"
_SCOPE_TMP_ROOT = _VAULT_ROOT / "runtime" / "tests" / "_tmp_browser_candidate_scope"
_SCOPE_WRITE_TMP_ROOT = _VAULT_ROOT / "runtime" / "tests" / "_tmp_browser_candidate_scope_write"


def _payload_from_output(text: str) -> dict:
    payload = json.loads(text)
    return payload.get("result", payload)


def _remove_tmp_vault(path: Path) -> None:
    for _attempt in range(3):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            time.sleep(0.1)
    shutil.rmtree(path, ignore_errors=True)


def _scoped_candidate_fixture_root() -> Path:
    if _SCOPE_TMP_ROOT.exists():
        _remove_tmp_vault(_SCOPE_TMP_ROOT)
    shutil.copytree(_FIXTURE_ROOT / "03_INPUTS", _SCOPE_TMP_ROOT / "03_INPUTS")
    shutil.copytree(
        _VAULT_ROOT / "runtime" / "siteops" / "catalog",
        _SCOPE_TMP_ROOT / "runtime" / "siteops" / "catalog",
    )
    shutil.copytree(
        _VAULT_ROOT / "runtime" / "siteops" / "tenants",
        _SCOPE_TMP_ROOT / "runtime" / "siteops" / "tenants",
    )
    return _SCOPE_TMP_ROOT


def _candidate_siteops_vault() -> Path:
    vault = _SCOPE_WRITE_TMP_ROOT
    if vault.exists():
        _remove_tmp_vault(vault)
    shutil.copytree(_FIXTURE_ROOT, vault)
    siteops_root = _VAULT_ROOT / "runtime" / "siteops"
    for name in ("catalog", "tenants"):
        shutil.copytree(siteops_root / name, vault / "runtime" / "siteops" / name, dirs_exist_ok=True)
    return vault


def test_candidate_records_scan_existing_candidate_home_without_raw_content() -> None:
    records = list_candidate_records(_FIXTURE_ROOT)

    assert len(records) == 1
    record = records[0]
    assert record["candidate_id"] == "candidate_run_123"
    assert record["proposed_skill_id"] == "example.safe_candidate"
    assert record["trust_tier"] == "Tier 4"
    assert record["raw_content_visible"] is False
    assert record["source_run_paths_visible"] is False
    assert record["validation"]["ok"] is True


def test_candidate_show_only_resolves_ids_from_scanned_candidate_store() -> None:
    by_candidate = show_candidate_record("candidate_run_123", _FIXTURE_ROOT)
    by_skill = show_candidate_record("example.safe_candidate", _FIXTURE_ROOT)

    assert by_candidate["path"] == by_skill["path"]
    with pytest.raises(BrowserSkillCandidateError):
        show_candidate_record("..\\secrets", _FIXTURE_ROOT)


def test_storage_reconciliation_names_bosl_candidate_home() -> None:
    storage = storage_reconciliation(_FIXTURE_ROOT)

    assert storage["candidate_home"] == "03_INPUTS/Browser-Skill-Candidates"
    assert storage["trusted_skill_home"] == "runtime/browser_skills/skills"
    assert "read-only inspection" in storage["siteops_boundary"]


def test_candidate_promotion_preflight_computes_non_mutating_target_preview() -> None:
    preflight = preflight_candidate_promotion("candidate_run_123", _FIXTURE_ROOT)

    assert preflight["ok"] is True
    assert preflight["candidate_id"] == "candidate_run_123"
    assert preflight["preflight_status"] == "ready_for_operator_review"
    assert preflight["writes_performed"] is False
    assert preflight["activation_allowed"] is False
    assert preflight["raw_content_visible"] is False
    assert preflight["target"]["path"] == "runtime/browser_skills/skills/example.safe_candidate.yaml"
    assert preflight["target"]["exists"] is False
    assert preflight["draft_preview"]["skill_id"] == "example.safe_candidate"
    assert preflight["draft_preview"]["step_count"] == 1
    assert "steps" not in preflight["draft_preview"]


def test_candidate_promotion_request_contract_stays_non_mutating_without_operator_write() -> None:
    from runtime.browser_skills.candidates import candidate_promotion_request_contract

    contract = candidate_promotion_request_contract(
        "candidate_run_123",
        _FIXTURE_ROOT,
        requested_by="local-user",
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
    )

    assert contract["ok"] is True
    assert contract["contract_status"] == "approval_request_ready"
    assert contract["scope"]["tenant_id"] == "local"
    assert contract["scope"]["workspace_id"] == "default"
    assert contract["scope"]["user_id"] == "local-user"
    assert contract["approval_required"] is True
    assert contract["approval_request_written"] is False
    assert contract["run_record_written"] is False
    assert contract["audit_event_written"] is False
    assert contract["trusted_skill_write_allowed"] is False
    assert contract["siteops_skill_card_write_allowed"] is False
    assert contract["browser_execution_allowed"] is False
    assert contract["approval_request"]["action"] == "browser_skill_candidate.promote"
    assert contract["approval_request"]["tenant_id"] == "local"
    assert contract["approval_request"]["workspace_id"] == "default"
    assert contract["approval_request"]["user_id"] == "local-user"
    assert contract["siteops_approval_preview"]["approval_ref_preview"].endswith(
        "07_LOGS/SiteOps-Approvals/local/default/"
        "approval_siteops_candidate_promotion_candidate_run_123_browser_skill_candidate_promote.json"
    )
    assert contract["approval_request"]["target"]["candidate_id"] == "candidate_run_123"
    assert contract["approval_request"]["target"]["trusted_skill_path"] == "runtime/browser_skills/skills/example.safe_candidate.yaml"


def test_scoped_candidate_request_aligns_scope_without_writing_artifacts() -> None:
    root = _scoped_candidate_fixture_root()
    try:
        payload = request_scoped_candidate_promotion(
            "candidate_run_123",
            root,
            tenant_id="local",
            workspace_id="default",
            user_id="local-user",
            requested_by="codex-scope-alignment",
            write_approval=False,
        )
    finally:
        _remove_tmp_vault(root)

    request = payload["approval_request"]
    assert payload["ok"] is True
    assert payload["scope"] == {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
    }
    assert request["scope"] == payload["scope"]
    assert request["requested_by"] == "codex-scope-alignment"
    assert payload["approval_request_written"] is False
    assert payload["siteops_run_written"] is False
    assert payload["audit_written"] is False
    assert payload["apply_contract"]["scope"] == payload["scope"]


def test_siteops_candidates_cli_list_show_preflight_and_request_are_json_enveloped(capsys: pytest.CaptureFixture[str]) -> None:
    list_code = cli.main(["siteops", "candidates", "list", "--vault-root", str(_FIXTURE_ROOT), "--json"])
    list_payload = _payload_from_output(capsys.readouterr().out)

    show_code = cli.main(
        [
            "siteops",
            "candidates",
            "show",
            "candidate_run_123",
            "--vault-root",
            str(_FIXTURE_ROOT),
            "--json",
        ]
    )
    show_payload = _payload_from_output(capsys.readouterr().out)

    preflight_code = cli.main(
        [
            "siteops",
            "candidates",
            "preflight",
            "candidate_run_123",
            "--vault-root",
            str(_FIXTURE_ROOT),
            "--json",
        ]
    )
    preflight_payload = _payload_from_output(capsys.readouterr().out)

    request_code = cli.main(
        [
            "siteops",
            "candidates",
            "request-promotion",
            "candidate_run_123",
            "--requested-by",
            "local-user",
            "--vault-root",
            str(_FIXTURE_ROOT),
            "--json",
        ]
    )
    request_payload = _payload_from_output(capsys.readouterr().out)

    assert list_code == 0
    assert list_payload["ok"] is True
    assert list_payload["count"] == 1
    assert list_payload["raw_content_visible"] is False
    assert show_code == 0
    assert show_payload["ok"] is True
    assert show_payload["candidate"]["candidate_id"] == "candidate_run_123"
    assert show_payload["activation_allowed"] is False
    assert preflight_code == 0
    assert preflight_payload["ok"] is True
    assert preflight_payload["preflight_status"] == "ready_for_operator_review"
    assert preflight_payload["writes_performed"] is False
    assert request_code == 0
    assert request_payload["ok"] is True
    assert request_payload["contract_status"] == "approval_request_ready"
    assert request_payload["scope"]["tenant_id"] == "local"
    assert request_payload["scope"]["workspace_id"] == "default"
    assert request_payload["scope"]["user_id"] == "local-user"
    assert request_payload["approval_request_written"] is False
    assert request_payload["run_record_written"] is False
    assert request_payload["audit_event_written"] is False
    assert request_payload["trusted_skill_write_allowed"] is False


def test_siteops_candidates_request_promotion_write_approval_request_only_persists_siteops_artifacts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    vault = _candidate_siteops_vault()
    try:
        code = cli.main(
            [
                "siteops",
                "candidates",
                "request-promotion",
                "candidate_run_123",
                "--requested-by",
                "local-user",
                "--tenant",
                "local",
                "--workspace",
                "default",
                "--user",
                "local-user",
                "--write-approval",
                "--vault-root",
                str(vault),
                "--json",
            ]
        )
        payload = _payload_from_output(capsys.readouterr().out)

        assert code == 0
        assert payload["ok"] is True
        assert payload["approval_request_written"] is True
        assert payload["siteops_run_written"] is True
        assert payload["audit_written"] is True
        assert payload["writes_performed"] is True
        assert payload["approval"]["status"] == "pending"
        assert payload["approval"]["action"] == "browser_skill_candidate.promote"
        assert Path(payload["approval"]["approval_ref"]).exists()
        assert Path(payload["run_ref"]).exists()
        assert Path(payload["audit_ref"]).exists()
        assert payload["trusted_skill_write_allowed"] is False
        assert payload["siteops_skill_card_write_allowed"] is False
        assert payload["browser_execution_allowed"] is False
        assert payload["activation_allowed"] is False
        assert payload["promotion_allowed"] is False
        assert not (vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    finally:
        _remove_tmp_vault(vault)


def test_candidate_promotion_apply_contract_reads_pending_approval_without_writing_skill() -> None:
    vault = _candidate_siteops_vault()
    try:
        request_payload = request_scoped_candidate_promotion(
            "candidate_run_123",
            vault,
            tenant_id="local",
            workspace_id="default",
            user_id="local-user",
            requested_by="apply-contract-test",
            write_approval=True,
        )
        approval_id = request_payload["approval"]["approval_id"]

        apply_payload = candidate_promotion_apply_contract(
            "candidate_run_123",
            vault,
            approval_id=approval_id,
            tenant_id="local",
            workspace_id="default",
            user_id="local-user",
        )

        assert apply_payload["ok"] is True
        assert apply_payload["writes_performed"] is False
        assert apply_payload["approval"]["status"] == "pending"
        assert apply_payload["apply_contract"]["apply_contract_status"] == "blocked_pending_approval"
        assert apply_payload["apply_contract"]["requires_future_gate_apply"] is True
        assert apply_payload["trusted_skill_write_allowed"] is False
        assert apply_payload["siteops_skill_card_write_allowed"] is False
        assert apply_payload["browser_execution_allowed"] is False
        assert apply_payload["activation_allowed"] is False
        assert not (vault / "runtime" / "browser_skills" / "skills" / "example.safe_candidate.yaml").exists()
    finally:
        _remove_tmp_vault(vault)
