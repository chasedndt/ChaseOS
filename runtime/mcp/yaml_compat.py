"""Small YAML compatibility layer for Runtime MCP.

Runtime MCP V1 is stdlib-first. If PyYAML is available, use it. Otherwise,
parse the simple mapping/list YAML shapes used by MCP config, workflow
manifests, and role cards.
"""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover - exercised only when PyYAML is installed.
    import yaml as _pyyaml
except ModuleNotFoundError:  # pragma: no cover - the fallback is covered.
    _pyyaml = None


def safe_load(text: str) -> Any:
    if _pyyaml is not None:
        return _pyyaml.safe_load(text)
    return _MiniYAML(text).parse()


class _MiniYAML:
    def __init__(self, text: str) -> None:
        self.lines = self._preprocess(text)

    def _preprocess(self, text: str) -> list[tuple[int, str]]:
        rows: list[tuple[int, str]] = []
        for raw in text.splitlines():
            if not raw.strip() or raw.strip() == "---" or raw.lstrip().startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            content = self._strip_inline_comment(raw.strip())
            if content:
                rows.append((indent, content))
        return rows

    def _strip_inline_comment(self, value: str) -> str:
        quote: str | None = None
        for index, char in enumerate(value):
            if char in {"'", '"'}:
                quote = None if quote == char else char if quote is None else quote
            if char == "#" and quote is None and index > 0 and value[index - 1].isspace():
                return value[:index].rstrip()
        return value

    def parse(self) -> Any:
        if not self.lines:
            return None
        data, _ = self._parse_block(0, self.lines[0][0])
        return data

    def _parse_block(self, index: int, indent: int) -> tuple[Any, int]:
        if index >= len(self.lines):
            return {}, index
        _, content = self.lines[index]
        if content.startswith("- "):
            return self._parse_list(index, indent)
        return self._parse_mapping(index, indent)

    def _parse_mapping(self, index: int, indent: int) -> tuple[dict[str, Any], int]:
        result: dict[str, Any] = {}
        while index < len(self.lines):
            row_indent, content = self.lines[index]
            if row_indent < indent:
                break
            if row_indent > indent:
                break
            if content.startswith("- "):
                break
            if ":" not in content:
                index += 1
                continue
            key, value = content.split(":", 1)
            key = key.strip().strip("'\"")
            value = value.strip()
            if value in {">", "|"}:
                block_lines: list[str] = []
                index += 1
                while index < len(self.lines) and self.lines[index][0] > row_indent:
                    block_lines.append(self.lines[index][1])
                    index += 1
                result[key] = "\n".join(block_lines)
            elif value:
                result[key] = self._parse_scalar(value)
                index += 1
            else:
                index += 1
                if index < len(self.lines) and self.lines[index][0] > row_indent:
                    nested, index = self._parse_block(index, self.lines[index][0])
                    result[key] = nested
                else:
                    result[key] = None
        return result, index

    def _parse_list(self, index: int, indent: int) -> tuple[list[Any], int]:
        result: list[Any] = []
        while index < len(self.lines):
            row_indent, content = self.lines[index]
            if row_indent < indent or not content.startswith("- "):
                break
            if row_indent > indent:
                break
            item = content[2:].strip()
            if not item:
                index += 1
                if index < len(self.lines) and self.lines[index][0] > row_indent:
                    nested, index = self._parse_block(index, self.lines[index][0])
                    result.append(nested)
                else:
                    result.append(None)
            elif ":" in item and not item.startswith(("'", '"')):
                key, value = item.split(":", 1)
                result.append({key.strip(): self._parse_scalar(value.strip())})
                index += 1
            else:
                result.append(self._parse_scalar(item))
                index += 1
        return result, index

    def _parse_scalar(self, value: str) -> Any:
        if value in {"", "null", "Null", "NULL", "~"}:
            return None
        if value in {"true", "True", "TRUE"}:
            return True
        if value in {"false", "False", "FALSE"}:
            return False
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]
        return value
