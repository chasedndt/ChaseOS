"""Pass 6 governance/advanced productization readback tests."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONTEND = ROOT / "runtime" / "studio" / "shell" / "frontend"


def _read(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def test_governance_panels_use_product_language_and_safe_posture():
    html = _read("index.html")

    expected = [
        "<h2>Approvals</h2>",
        "Digest review",
        "No execution",
        "<h2>Logs / Audit</h2>",
        "No log writes",
        "<h2>Decisions</h2>",
        "No decision write",
        "<h2>Settings</h2>",
        "Secrets hidden",
        "No host mutation",
        "<h2>Feature Audit</h2>",
        "Adoption Gate SOP",
        "No roadmap write",
    ]
    for token in expected:
        assert token in html


def test_advanced_panels_use_product_language_and_safe_posture():
    html = _read("index.html")

    expected = [
        "<h2>Site Skills</h2>",
        "No deployment",
        "No browser control",
        "No execution",
        "No trust change",
        "No workflow run",
        "No routing grant",
    ]
    for token in expected:
        assert token in html


def test_governance_and_advanced_surfaces_wire_selection_to_inspector():
    app = _read("app.js")

    expected = [
        "Selected Approval",
        "Selected Audit Log",
        "Selected Decision",
        "Selected Feature Rule",
        "Selected Workflow",
        "Selected Role Card",
        "Selected Surface",
        "Selected Browser Runtime Item",
        "Selected Runtime Map",
        "Selected Provider",
        "Selected Site Skill Run",
        "Selected Site Skill Approval",
    ]
    for token in expected:
        assert token in app


def test_governance_and_advanced_click_targets_have_selection_affordance():
    css = _read("styles.css")

    expected = [
        ".approval-queue-item",
        ".build-log-item",
        ".decision-item",
        ".ff-task-item",
        ".workflow-item",
        ".role-card-item",
        ".app-launcher-card",
        ".browser-runtime-list-item",
        ".settings-info-pill",
        ".rnm-runtime-card",
        ".siteops-run-card",
        ".siteops-approval-card",
    ]
    for token in expected:
        assert token in css

