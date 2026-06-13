from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.acquisition.adapters.visual_capture_adapter import (
    VisualCapturePreviewError,
    preview_visual_capture_acquisition,
)
from runtime.capture.visual_capture import (
    VisualCaptureReviewStateError,
    review_visual_capture_artifact,
    save_visual_capture,
)
from runtime.capture.visual_capture import review_state as review_state_module


def _save_capture(vault: Path, *, title: str = "VCMI Review Target", text: str = "Visible source text.") -> dict:
    return save_visual_capture(
        vault_root=vault,
        title=title,
        profile="research_note",
        capture_method="manual_paste",
        raw_extracted_text=text,
        user_intent="Prepare a reviewed acquisition preview.",
        captured_at="2026-05-20T13:00:00Z",
        capture_id=f"vcmi_20260520130000_{abs(hash(title))}",
    )


def _rel(path: str | Path, root: Path) -> str:
    return Path(path).resolve().relative_to(root.resolve()).as_posix()


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_write_json_retries_transient_windows_replace_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "state.json"
    target.write_text("{}", encoding="utf-8")
    original_replace = Path.replace
    calls = {"count": 0}

    def flaky_replace(self: Path, destination: str | Path) -> Path:
        if self.name == "state.json.tmp" and calls["count"] == 0:
            calls["count"] += 1
            raise PermissionError("transient Windows file lock")
        calls["count"] += 1
        return original_replace(self, destination)

    monkeypatch.setattr(review_state_module, "JSON_REPLACE_RETRY_DELAYS_SECONDS", (0.0,))
    monkeypatch.setattr(Path, "replace", flaky_replace)

    review_state_module._write_json(target, {"ok": True})

    assert calls["count"] == 2
    assert json.loads(target.read_text(encoding="utf-8")) == {"ok": True}


def test_reviewed_state_updates_sidecar_and_packet_then_unlocks_acquisition_preview(tmp_path: Path) -> None:
    saved = _save_capture(tmp_path)
    content_path = Path(saved["content_path"])
    content_before = content_path.read_text(encoding="utf-8")

    result = review_visual_capture_artifact(
        tmp_path,
        _rel(saved["content_path"], tmp_path),
        decision="reviewed",
        reviewed_by="operator",
        review_note="source checked",
    )

    assert result["ok"] is True
    assert result["status"] == "review_state_updated"
    assert result["old_status"] == "pending-review"
    assert result["new_status"] == "reviewed"
    assert result["content_write_performed"] is False
    assert result["sidecar_write_performed"] is True
    assert result["visual_capture_packet_json_write_performed"] is True
    assert result["authority"]["canonical_mutation_allowed"] is False
    assert content_path.read_text(encoding="utf-8") == content_before

    sidecar = _load_json(saved["sidecar_path"])
    vc_meta = sidecar["extra_metadata"]["visual_capture"]
    assert sidecar["quarantine_status"] == "reviewed"
    assert sidecar["review_status"] == "reviewed"
    assert sidecar["promotion_status"] == "quarantine"
    assert sidecar["source_package_status"] == "not-ingested"
    assert vc_meta["review_status"] == "reviewed"
    assert vc_meta["requires_review"] is False
    assert vc_meta["canonical_status"] == "not_promoted"
    assert sidecar["operator_review_state"]["decision_id"] == result["decision_id"]
    assert sidecar["review_history"][-1]["new_status"] == "reviewed"

    packet = _load_json(saved["visual_capture_packet_path"])
    assert packet["routing"]["review_status"] == "reviewed"
    assert packet["routing"]["requires_review"] is False
    assert packet["routing"]["canonical_status"] == "not_promoted"
    assert packet["routing"]["source_package_status"] == "not-ingested"
    assert packet["routing"]["aor_queue_status"] == "not_queued"
    assert packet["provenance"]["transformation_chain"][-1]["step"] == "operator_review_state_update"

    preview = preview_visual_capture_acquisition(tmp_path, _rel(saved["visual_capture_packet_path"], tmp_path))
    assert preview["ok"] is True
    assert preview["status"] == "preview_ready"
    assert preview["write_performed"] is False
    assert not (tmp_path / "02_KNOWLEDGE").exists()
    assert not (tmp_path / "runtime" / "source_intelligence").exists()


def test_rejected_state_remains_quarantine_and_blocks_acquisition_preview(tmp_path: Path) -> None:
    saved = _save_capture(tmp_path, title="Rejected Review Target")

    result = review_visual_capture_artifact(
        tmp_path,
        saved["sidecar_path"],
        decision="rejected",
        reviewed_by="operator",
    )

    assert result["new_status"] == "rejected"
    sidecar = _load_json(saved["sidecar_path"])
    assert sidecar["quarantine_status"] == "rejected"
    assert sidecar["extra_metadata"]["visual_capture"]["canonical_status"] == "not_promoted"

    with pytest.raises(VisualCapturePreviewError, match="must be reviewed"):
        preview_visual_capture_acquisition(tmp_path, _rel(saved["content_path"], tmp_path))


def test_illegal_review_transition_fails_closed_without_rewriting_state(tmp_path: Path) -> None:
    saved = _save_capture(tmp_path, title="Illegal Transition Review Target")
    review_visual_capture_artifact(tmp_path, saved["content_path"], decision="reviewed", reviewed_by="operator")

    with pytest.raises(VisualCaptureReviewStateError, match="reviewed -> rejected"):
        review_visual_capture_artifact(tmp_path, saved["content_path"], decision="rejected", reviewed_by="operator")

    sidecar = _load_json(saved["sidecar_path"])
    assert sidecar["quarantine_status"] == "reviewed"
    assert sidecar["review_history"][-1]["new_status"] == "reviewed"


def test_review_state_dry_run_validates_without_writing(tmp_path: Path) -> None:
    saved = _save_capture(tmp_path, title="Dry Run Review Target")

    result = review_visual_capture_artifact(
        tmp_path,
        saved["visual_capture_packet_path"],
        decision="needs-redaction",
        reviewed_by="operator",
        dry_run=True,
    )

    assert result["status"] == "review_state_dry_run"
    assert result["write_performed"] is False
    sidecar = _load_json(saved["sidecar_path"])
    packet = _load_json(saved["visual_capture_packet_path"])
    assert sidecar["quarantine_status"] == "pending-review"
    assert sidecar["extra_metadata"]["visual_capture"]["review_status"] == "pending-review"
    assert packet["routing"]["review_status"] == "pending-review"


def test_review_state_blocks_non_quarantine_paths_without_writes(tmp_path: Path) -> None:
    content = tmp_path / "not-quarantine.md"
    sidecar = tmp_path / "not-quarantine.meta.json"
    content.write_text("Reviewed text outside quarantine.", encoding="utf-8")
    sidecar_payload = {
        "schema_version": "8.3",
        "capture_id": "outside",
        "content_filename": content.name,
        "content_sha256": "abc",
        "title": "Outside",
        "captured_at": "2026-05-20T13:00:00Z",
        "quarantine_status": "pending-review",
        "promotion_status": "quarantine",
        "source_package_status": "not-ingested",
        "extra_metadata": {
            "visual_capture": {
                "schema_version": "vcmi.v0.1",
                "capture_id": "vcmi_20260520130000_outside",
                "review_status": "pending-review",
                "canonical_status": "not_promoted",
            }
        },
    }
    sidecar.write_text(json.dumps(sidecar_payload, indent=2), encoding="utf-8")
    before = sidecar.read_text(encoding="utf-8")

    with pytest.raises(VisualCaptureReviewStateError, match="03_INPUTS/00_QUARANTINE"):
        review_visual_capture_artifact(tmp_path, content, decision="reviewed", reviewed_by="operator")

    assert sidecar.read_text(encoding="utf-8") == before


def test_review_note_secret_like_text_blocks_without_writes(tmp_path: Path) -> None:
    saved = _save_capture(tmp_path, title="Secret Note Review Target")
    raw_secret = "api_key=test-key-abcdefghijklmnopqrstuvwxyz123456"

    with pytest.raises(VisualCaptureReviewStateError, match="review_note contains secret-like material"):
        review_visual_capture_artifact(
            tmp_path,
            saved["content_path"],
            decision="reviewed",
            reviewed_by="operator",
            review_note=f"contains {raw_secret}",
        )

    sidecar = _load_json(saved["sidecar_path"])
    assert sidecar["quarantine_status"] == "pending-review"
    assert raw_secret not in json.dumps(sidecar)
