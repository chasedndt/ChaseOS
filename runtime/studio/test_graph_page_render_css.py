"""Regression tests for the native Studio Graph route render surface."""

from __future__ import annotations

import re
from pathlib import Path


FRONTEND_DIR = Path(__file__).parent / "shell" / "frontend"


def _css_rule(selector: str) -> str:
    css = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>.*?)\}}", css, flags=re.DOTALL)
    assert match is not None, f"missing CSS rule for {selector}"
    return match.group("body")


def test_graph_panel_preserves_absolute_shell_panel_mount() -> None:
    """Graph route must fill #main; a relative override collapses #cy to 0px."""

    rule = _css_rule("#panel-graph")

    assert re.search(r"position\s*:\s*absolute\s*;", rule)
    assert re.search(r"inset\s*:\s*0\s*;", rule)


def test_graph_canvas_has_nonzero_render_floor() -> None:
    """Cytoscape needs a non-zero container height before it can draw nodes."""

    rule = _css_rule("#cy")

    assert "min-height: 0" not in rule
    assert re.search(r"min-height\s*:\s*(?:2[4-9]\d|[3-9]\d\d)px\s*;", rule)
