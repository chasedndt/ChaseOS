from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_hermes_capability_manifest_advertises_bounded_chat_task_type():
    data = yaml.safe_load((ROOT / "runtime" / "hermes" / "capabilities.yaml").read_text(encoding="utf-8"))

    handles = {entry["task_type"]: entry for entry in data["handles"]}

    assert "chat" in handles
    assert handles["chat"]["priority"] == "secondary"
    assert "Studio Chat" in handles["chat"]["notes"]
    assert "no shell" in handles["chat"]["notes"].lower()


def test_hermes_adapter_policy_allows_bounded_chat_task_type():
    data = yaml.safe_load((ROOT / "runtime" / "policy" / "adapters" / "hermes.yaml").read_text(encoding="utf-8"))

    assert "chat" in data["allowed_task_types"]
    notes = data["notes"]
    assert "chat" in notes.lower()
    assert "no shell" in notes.lower()
    assert "no canonical promotion" in notes.lower()
