"""Shared readiness helpers for Pulse product-shell browser QA evidence."""

from __future__ import annotations

from pathlib import Path


PRODUCT_SHELL_ROOT = Path("07_LOGS") / "Pulse-Decks" / "product-shell"
PULSE_PRODUCT_SHELL_BROWSER_QA_PASS = "chaseos-pulse-product-shell-browser-qa-and-studio-mount-contract"
NEXT_PULSE_PRODUCT_SHELL_PASS_AFTER_BROWSER_QA = "chaseos-pulse-product-shell-studio-panel-contract"
NEXT_PULSE_PRODUCT_SHELL_PASS_AFTER_PANEL_CONTRACT = "chaseos-pulse-studio-product-shell-mount"
PULSE_PRODUCT_SHELL_PANEL_CONTRACT_PATH = Path("runtime") / "studio" / "pulse_product_shell_panel.py"
PULSE_PRODUCT_SHELL_STUDIO_MOUNT_DOC_PATH = (
    Path("06_AGENTS") / "ChaseOS-Pulse-Studio-Product-Shell-Mount.md"
)


def latest_pulse_product_shell_artifact(vault_root: str | Path | None) -> Path | None:
    """Return the newest persisted Pulse product-shell artifact, if one exists."""

    if vault_root is None or str(vault_root) == "":
        return None
    artifact_root = Path(vault_root).resolve() / PRODUCT_SHELL_ROOT
    if not artifact_root.exists():
        return None
    candidates = [path for path in artifact_root.glob("*pulse-product-shell.html") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def pulse_product_shell_browser_qa_evidence_built(vault_root: str | Path | None) -> bool:
    """Return true when durable Pulse product-shell browser-QA evidence exists."""

    return latest_pulse_product_shell_browser_qa_note(vault_root) is not None


def latest_pulse_product_shell_browser_qa_note(vault_root: str | Path | None) -> Path | None:
    """Return the newest Pulse product-shell browser-QA note, if one exists."""

    if vault_root is None or str(vault_root) == "":
        return None
    evidence_root = Path(vault_root).resolve() / PRODUCT_SHELL_ROOT
    if not evidence_root.exists():
        return None
    candidates = [path for path in evidence_root.glob("*product-shell-browser-qa.md") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def latest_pulse_product_shell_browser_qa_screenshot(vault_root: str | Path | None) -> Path | None:
    """Return the screenshot paired to the newest browser-QA note, if it exists."""

    if vault_root is None or str(vault_root) == "":
        return None
    evidence_root = Path(vault_root).resolve() / PRODUCT_SHELL_ROOT
    if not evidence_root.exists():
        return None
    latest_note = latest_pulse_product_shell_browser_qa_note(vault_root)
    if latest_note is None:
        return None
    paired_screenshot = latest_note.with_suffix(".png")
    if paired_screenshot.is_file():
        return paired_screenshot
    return None


def pulse_product_shell_panel_contract_built(vault_root: str | Path | None) -> bool:
    """Return true when the Pulse product-shell panel contract exists."""

    if vault_root is None or str(vault_root) == "":
        return False
    return (Path(vault_root).resolve() / PULSE_PRODUCT_SHELL_PANEL_CONTRACT_PATH).is_file()


def pulse_product_shell_studio_mount_built(vault_root: str | Path | None) -> bool:
    """Return true when the read-only Pulse product shell Studio mount is documented and coded."""

    if vault_root is None or str(vault_root) == "":
        return False
    vault = Path(vault_root).resolve()
    return (
        (vault / PULSE_PRODUCT_SHELL_PANEL_CONTRACT_PATH).is_file()
        and (vault / "runtime" / "studio" / "desktop_shell_app.py").is_file()
        and (vault / PULSE_PRODUCT_SHELL_STUDIO_MOUNT_DOC_PATH).is_file()
        and latest_pulse_product_shell_artifact(vault) is not None
        and pulse_product_shell_browser_qa_evidence_built(vault)
    )


def next_pulse_product_shell_pass_after_browser_qa(vault_root: str | Path | None) -> str:
    """Return the next Pulse product-shell pass after browser QA for this workspace."""

    if pulse_product_shell_studio_mount_built(vault_root):
        return "chaseos-pulse-interactive-governed-controls"
    if pulse_product_shell_panel_contract_built(vault_root):
        return NEXT_PULSE_PRODUCT_SHELL_PASS_AFTER_PANEL_CONTRACT
    return NEXT_PULSE_PRODUCT_SHELL_PASS_AFTER_BROWSER_QA
