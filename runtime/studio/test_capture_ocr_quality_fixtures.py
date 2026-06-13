from __future__ import annotations

import json
import sys
from pathlib import Path

from runtime.studio.capture_ocr_quality_fixtures import (
    build_capture_local_image_text_quality_fixture_model,
    run_capture_local_image_text_quality_fixtures,
)


def _write_fixture_text_engine(vault_root: Path) -> str:
    script = vault_root / "runtime" / "capture" / "fake-fixture-text-engine.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "from __future__ import annotations\n"
        "from pathlib import Path\n"
        "import sys\n"
        "name = Path(sys.argv[1]).stem if len(sys.argv) > 1 else ''\n"
        "responses = {\n"
        "    'no_text': '',\n"
        "    'dense_text': 'CHASEOS MARKDOWN CAPTURE VISIBLE TEXT LOCAL ENGINE',\n"
        "    'low_contrast': 'LOW CONTRAST CAPTURE READABILITY CHECK',\n"
        "    'table_text': 'ITEM COUNT STATUS ALPHA 12 BETA 34 REVIEW',\n"
        "    'mixed_language': 'MIXED LANGUAGE HOLA BONJOUR CAFE RESUME NAIVE',\n"
        "    'studio_font_screenshot': 'CAPTURE MARKDOWN SCREEN TEXT STUDIO DISCORD BROWSER READY',\n"
        "}\n"
        "print(responses.get(name, ''))\n",
        encoding="utf-8",
    )
    return json.dumps([sys.executable, str(script)])


def test_capture_local_image_text_quality_model_is_read_only_when_no_engine(tmp_path: Path) -> None:
    model = build_capture_local_image_text_quality_fixture_model(
        tmp_path,
        command=["missing-local-image-text-engine"],
    )

    assert model["surface"] == "studio_capture_local_image_text_quality_fixtures"
    assert model["status"] == "blocked_missing_local_engine"
    assert model["summary"]["fixture_runner_ready"] is True
    assert model["summary"]["real_engine_quality_verified"] is False
    assert model["authority"]["writes_on_settings_load"] is False
    assert model["authority"]["writes_raw_quarantine_markdown"] is False
    assert not (tmp_path / "07_LOGS").exists()


def test_capture_local_image_text_quality_runner_blocks_without_engine(tmp_path: Path) -> None:
    report = run_capture_local_image_text_quality_fixtures(
        tmp_path,
        command=["missing-local-image-text-engine"],
        run_id="missing-engine",
        write_report=True,
        use_saved_settings=False,
    )

    assert report["status"] == "blocked_missing_local_engine"
    assert report["summary"]["real_engine_quality_verified"] is False
    assert report["summary"]["raw_quarantine_markdown_written"] is False
    assert report["summary"]["provider_calls_performed"] is False
    assert report["summary"]["live_screen_capture_performed"] is False
    assert all(item["blocked"] is True for item in report["fixtures"])
    assert Path(report["report_path"]).is_file()
    assert Path(report["markdown_report_path"]).is_file()
    assert (tmp_path / "07_LOGS" / "Operator-Screenshots" / "Capture-OCR-Fixtures" / "missing-engine").is_dir()
    assert not (tmp_path / "03_INPUTS").exists()


def test_capture_local_image_text_quality_runner_verifies_fake_fixture_engine(tmp_path: Path) -> None:
    command = _write_fixture_text_engine(tmp_path)

    report = run_capture_local_image_text_quality_fixtures(
        tmp_path,
        command=command,
        run_id="fake-engine",
        write_report=True,
        use_saved_settings=False,
    )

    assert report["status"] == "verified"
    assert report["ok"] is True
    assert report["summary"]["real_engine_quality_verified"] is True
    assert report["summary"]["passed_fixture_count"] == 6
    assert report["summary"]["failed_fixture_count"] == 0
    assert report["summary"]["blocked_fixture_count"] == 0
    assert {item["id"] for item in report["fixtures"]} == {
        "no_text",
        "dense_text",
        "low_contrast",
        "table_text",
        "mixed_language",
        "studio_font_screenshot",
    }
    assert all(item["passed"] for item in report["fixtures"])
    assert Path(report["report_path"]).is_file()
    assert Path(report["markdown_report_path"]).is_file()
    assert not (tmp_path / "03_INPUTS").exists()

    model = build_capture_local_image_text_quality_fixture_model(tmp_path, command=command)
    assert model["status"] == "quality_verified"
    assert model["latest_report"]["real_engine_quality_verified"] is True
