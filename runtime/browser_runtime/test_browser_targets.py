"""Tests for known Browser Runtime target registry."""

from __future__ import annotations

import pytest

from runtime.browser_runtime.browser_targets import (
    get_known_browser_target,
    list_known_browser_targets,
)


def test_excalidraw_known_target_requires_no_env_url() -> None:
    target = get_known_browser_target("excalidraw")

    assert target.url == "https://excalidraw.com"
    assert target.allowed_domains == ("excalidraw.com",)
    assert target.public_target is True
    assert target.login_required is False
    assert target.env_required is False


def test_known_targets_are_listed() -> None:
    target_ids = {target.target_id for target in list_known_browser_targets()}

    assert "excalidraw" in target_ids


def test_unknown_target_blocks() -> None:
    with pytest.raises(ValueError, match="unknown browser target"):
        get_known_browser_target("unknown")

