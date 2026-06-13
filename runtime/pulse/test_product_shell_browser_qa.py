from __future__ import annotations

from pathlib import Path

from runtime.pulse.product_shell_browser_qa import (
    latest_pulse_product_shell_browser_qa_note,
    latest_pulse_product_shell_browser_qa_screenshot,
)


def test_browser_qa_screenshot_must_match_latest_note(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    evidence = vault / "07_LOGS" / "Pulse-Decks" / "product-shell"
    evidence.mkdir(parents=True)

    old_note = evidence / "2026-05-03-pulse-product-shell-browser-qa.md"
    old_note.write_text("old", encoding="utf-8")
    old_png = evidence / "2026-05-03-pulse-product-shell-browser-qa.png"
    old_png.write_bytes(b"png")

    new_note = evidence / "2026-05-03-six-panel-product-shell-browser-qa.md"
    new_note.write_text("new", encoding="utf-8")

    assert latest_pulse_product_shell_browser_qa_note(vault) == new_note
    assert latest_pulse_product_shell_browser_qa_screenshot(vault) is None

    new_png = evidence / "2026-05-03-six-panel-product-shell-browser-qa.png"
    new_png.write_bytes(b"png")

    assert latest_pulse_product_shell_browser_qa_screenshot(vault) == new_png
