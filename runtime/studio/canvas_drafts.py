"""Read-only workspace-local Canvas draft schema and loader for Studio Phase 10E.

This module is intentionally schema/loader only. It reads JSON canvas drafts from
``runtime/studio/canvas_drafts/`` and returns authority flags that keep Phase 10E
separate from canonical graph truth, provenance writes, source-package writes,
and browser/Excalidraw control.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "studio_canvas.v1"
CANVAS_DRAFT_DIR = "runtime/studio/canvas_drafts"
SURFACE_ID = "studio_canvas_draft_loader"
SAVE_SURFACE_ID = "studio_canvas_draft_save"

CANVAS_AUTHORITY_FLAGS: dict[str, bool] = {
    "canonical_mutation_allowed": False,
    "graph_mutation_allowed": False,
    "promotion_requires_gate": True,
    "browser_control_allowed": False,
}

CANVAS_BLOCKED_AUTHORITY = [
    "canonical_mutation",
    "graph_mutation",
    "provenance_write",
    "source_package_write",
    "browser_control",
]

CANVAS_SAVE_BLOCKED_AUTHORITY = [
    "markdown_note_conversion",
    "graph_link_conversion",
    "graph_snapshot_write",
    "provenance_write",
    "source_package_write",
    "canonical_knowledge_write",
    "browser_control",
]

CANVAS_WRITE_CONTRACT: dict[str, bool] = {
    "markdown_writes": False,
    "graph_snapshot_writes": False,
    "provenance_writes": False,
    "source_package_writes": False,
    "browser_actions": False,
    "canonical_writes": False,
}

CANVAS_SAVE_WRITE_CONTRACT: dict[str, bool] = {
    "canvas_draft_json_writes": True,
    "markdown_writes": False,
    "graph_link_writes": False,
    "graph_snapshot_writes": False,
    "provenance_writes": False,
    "source_package_writes": False,
    "browser_actions": False,
    "canonical_writes": False,
}

CANVAS_SAVE_WRITE_POLICY: dict[str, bool | str] = {
    "allowed_local_draft_write": True,
    "allowed_local_draft_root": CANVAS_DRAFT_DIR,
    "approval_required_for_canonical_conversion": True,
    "markdown_note_conversion_preview_only": True,
    "graph_link_conversion_preview_only": True,
    "graph_snapshot_preview_only": True,
    "provenance_record_preview_only": True,
    "source_package_preview_only": True,
    "canonical_knowledge_preview_only": True,
}

CANVAS_SAVE_BLOCKED_AUTHORITY_REASONS: dict[str, str] = {
    "markdown_note_conversion": "blocked: markdown note conversion requires approval and remains preview-only",
    "graph_link_conversion": "blocked: graph link conversion requires approval and remains preview-only",
    "graph_snapshot_write": "blocked: graph snapshot writes require approval and remain preview-only",
    "provenance_write": "blocked: provenance record writes require approval and remain preview-only",
    "source_package_write": "blocked: source package writes require approval and remain preview-only",
    "canonical_knowledge_write": "blocked: canonical knowledge writes require Gate approval and remain preview-only",
    "browser_control": "blocked: browser/Excalidraw control is outside the local Canvas draft-save boundary",
}

_ALLOWED_OBJECT_KINDS = frozenset(
    {
        "graph_node_ref",
        "note_card",
        "group",
        "image_ref",
        "artifact_ref",
        "proposal_card",
    }
)
_ALLOWED_LINK_KINDS = frozenset({"canvas_visual_link"})


class CanvasDraftError(ValueError):
    """Validation or loading failure for a workspace-local canvas draft."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


@dataclass(frozen=True)
class CanvasObject:
    """JSON-serializable visual object inside a CanvasDocument."""

    object_id: str
    kind: str
    label: str
    position: dict[str, Any]
    size: dict[str, Any]
    style: dict[str, Any] = field(default_factory=dict)
    target_ref: dict[str, Any] | None = None
    draft_text: str | None = None
    created_by: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(cls, value: Any) -> "CanvasObject":
        if not isinstance(value, dict):
            raise CanvasDraftError("invalid_canvas_object", "CanvasObject must be an object")
        required = ("object_id", "kind", "label", "position", "size")
        _require_keys(value, required, code="invalid_canvas_object")
        obj = cls(
            object_id=_required_string(value, "object_id", code="invalid_canvas_object"),
            kind=_required_string(value, "kind", code="invalid_canvas_object"),
            label=_required_string(value, "label", code="invalid_canvas_object"),
            position=_required_mapping(value, "position", code="invalid_canvas_object"),
            size=_required_mapping(value, "size", code="invalid_canvas_object"),
            style=_optional_mapping(value, "style"),
            target_ref=_optional_mapping_or_none(value, "target_ref"),
            draft_text=_optional_string_or_none(value, "draft_text"),
            created_by=str(value.get("created_by") or ""),
            updated_at=str(value.get("updated_at") or ""),
        )
        obj.validate()
        return obj

    def validate(self) -> None:
        if self.kind not in _ALLOWED_OBJECT_KINDS:
            raise CanvasDraftError("invalid_object_kind", f"Unsupported canvas object kind: {self.kind}")
        _validate_xy(self.position, "position", code="invalid_canvas_object")
        _validate_size(self.size, code="invalid_canvas_object")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CanvasLink:
    """JSON-serializable visual link between canvas objects."""

    link_id: str
    source_object_id: str
    target_object_id: str
    label: str
    kind: str = "canvas_visual_link"
    canonical_edge_ref: str | None = None
    conversion: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: Any) -> "CanvasLink":
        if not isinstance(value, dict):
            raise CanvasDraftError("invalid_canvas_link", "CanvasLink must be an object")
        required = ("link_id", "source_object_id", "target_object_id", "label", "kind")
        _require_keys(value, required, code="invalid_canvas_link")
        link = cls(
            link_id=_required_string(value, "link_id", code="invalid_canvas_link"),
            source_object_id=_required_string(value, "source_object_id", code="invalid_canvas_link"),
            target_object_id=_required_string(value, "target_object_id", code="invalid_canvas_link"),
            label=_required_string(value, "label", code="invalid_canvas_link"),
            kind=_required_string(value, "kind", code="invalid_canvas_link"),
            canonical_edge_ref=_optional_string_or_none(value, "canonical_edge_ref"),
            conversion=_optional_mapping(value, "conversion"),
        )
        link.validate()
        return link

    def validate(self) -> None:
        if self.kind not in _ALLOWED_LINK_KINDS:
            raise CanvasDraftError("invalid_link_kind", f"Unsupported canvas link kind: {self.kind}")
        if self.canonical_edge_ref is not None:
            raise CanvasDraftError(
                "canonical_edge_ref_blocked",
                "Canvas visual links must not embed canonical graph edge references in the draft loader",
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CanvasDocument:
    """JSON-serializable Studio Canvas draft document."""

    schema_version: str
    canvas_id: str
    title: str
    created_at: str
    updated_at: str
    workspace_root_ref: str
    authority: dict[str, bool]
    objects: list[CanvasObject]
    links: list[CanvasLink]
    view_state: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: Any) -> "CanvasDocument":
        if not isinstance(value, dict):
            raise CanvasDraftError("invalid_canvas_document", "CanvasDocument must be a JSON object")
        required = (
            "schema_version",
            "canvas_id",
            "title",
            "created_at",
            "updated_at",
            "workspace_root_ref",
            "authority",
            "objects",
            "links",
            "view_state",
            "provenance",
        )
        _require_keys(value, required, code="invalid_canvas_document")
        objects_raw = value.get("objects")
        links_raw = value.get("links")
        if not isinstance(objects_raw, list):
            raise CanvasDraftError("invalid_canvas_document", "objects must be a list")
        if not isinstance(links_raw, list):
            raise CanvasDraftError("invalid_canvas_document", "links must be a list")
        document = cls(
            schema_version=_required_string(value, "schema_version", code="invalid_canvas_document"),
            canvas_id=_required_string(value, "canvas_id", code="invalid_canvas_document"),
            title=_required_string(value, "title", code="invalid_canvas_document"),
            created_at=_required_string(value, "created_at", code="invalid_canvas_document"),
            updated_at=_required_string(value, "updated_at", code="invalid_canvas_document"),
            workspace_root_ref=_required_string(value, "workspace_root_ref", code="invalid_canvas_document"),
            authority=_authority(value.get("authority")),
            objects=[CanvasObject.from_dict(item) for item in objects_raw],
            links=[CanvasLink.from_dict(item) for item in links_raw],
            view_state=_required_mapping(value, "view_state", code="invalid_canvas_document"),
            provenance=_required_mapping(value, "provenance", code="invalid_canvas_document"),
        )
        document.validate()
        return document

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise CanvasDraftError("unsupported_schema_version", f"Unsupported canvas schema: {self.schema_version}")
        if self.authority != CANVAS_AUTHORITY_FLAGS:
            raise CanvasDraftError(
                "authority_boundary_violation",
                "Canvas drafts must report canonical=false, graph=false, promotion_requires_gate=true, browser=false",
            )
        if self.workspace_root_ref != ".":
            raise CanvasDraftError(
                "workspace_root_ref_blocked",
                "Canvas drafts must remain workspace-local with workspace_root_ref='.'",
            )
        object_ids = [obj.object_id for obj in self.objects]
        if len(object_ids) != len(set(object_ids)):
            raise CanvasDraftError("duplicate_canvas_object", "Canvas object IDs must be unique")
        object_id_set = set(object_ids)
        link_ids = [link.link_id for link in self.links]
        if len(link_ids) != len(set(link_ids)):
            raise CanvasDraftError("duplicate_canvas_link", "Canvas link IDs must be unique")
        for link in self.links:
            if link.source_object_id not in object_id_set or link.target_object_id not in object_id_set:
                raise CanvasDraftError(
                    "missing_canvas_object",
                    "Canvas links must reference existing canvas object IDs only",
                )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["objects"] = [obj.to_dict() for obj in self.objects]
        data["links"] = [link.to_dict() for link in self.links]
        return data


def canvas_authority_payload() -> dict[str, bool]:
    """Return a copy of the non-negotiable Canvas authority flags."""

    return dict(CANVAS_AUTHORITY_FLAGS)


def load_canvas_draft(vault_root: str | Path, draft_name: str) -> CanvasDocument:
    """Load and validate one JSON canvas draft from the constrained draft directory.

    ``draft_name`` is a filename or relative path under ``CANVAS_DRAFT_DIR``. Path
    traversal and non-JSON inputs are rejected before any file read.
    """

    path = _resolve_canvas_draft_path(vault_root, draft_name)
    if not path.is_file():
        raise CanvasDraftError("missing_canvas_draft", f"Canvas draft not found: {draft_name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CanvasDraftError("invalid_json", f"Canvas draft is not valid JSON: {exc.msg}") from exc
    return CanvasDocument.from_dict(payload)


def load_canvas_draft_response(vault_root: str | Path, draft_name: str) -> dict[str, Any]:
    """Return a JSON-serializable read-only loader envelope for Studio/API callers."""

    try:
        path = _resolve_canvas_draft_path(vault_root, draft_name)
        document = load_canvas_draft(vault_root, draft_name)
    except CanvasDraftError as exc:
        return _response_base(ok=False, status="blocked_or_failed") | {
            "error": {"code": exc.code, "message": exc.message},
        }
    return _response_base(ok=True, status="ok") | {
        "draft_path": path.relative_to(Path(vault_root).resolve()).as_posix(),
        "read_only": True,
        "document": document.to_dict(),
    }


def save_canvas_draft_response(vault_root: str | Path, draft_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and save one workspace-local JSON Canvas draft.

    This is the only Phase 10E local Canvas write allowed by this module. It is
    constrained to ``runtime/studio/canvas_drafts/*.json`` and validates the full
    draft schema before creating parent directories or writing bytes. Markdown
    note conversion, graph/link mutation, graph snapshots, provenance/source
    package writes, browser control, and canonical knowledge writes remain
    blocked/preview-only and are reported in every Studio-style envelope.
    """

    try:
        path = _resolve_canvas_draft_path(vault_root, draft_name)
        document = CanvasDocument.from_dict(payload)
    except CanvasDraftError as exc:
        return _save_response_base(ok=False, status="blocked_or_failed", target_block_reason=exc.message) | {
            "error": {"code": exc.code, "message": exc.message},
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _save_response_base(ok=True, status="ok") | {
        "draft_path": path.relative_to(Path(vault_root).resolve()).as_posix(),
        "read_only": False,
        "document": document.to_dict(),
    }


def _response_base(*, ok: bool, status: str) -> dict[str, Any]:
    return {
        "ok": ok,
        "status": status,
        "surface": SURFACE_ID,
        "authority": canvas_authority_payload(),
        "canonical_mutation_allowed": False,
        "graph_mutation_allowed": False,
        "promotion_requires_gate": True,
        "browser_control_allowed": False,
        "blocked_authority": list(CANVAS_BLOCKED_AUTHORITY),
        "write_contract": dict(CANVAS_WRITE_CONTRACT),
        "warnings": [],
    }


def _save_response_base(*, ok: bool, status: str, target_block_reason: str = "") -> dict[str, Any]:
    return {
        "ok": ok,
        "status": status,
        "surface": SAVE_SURFACE_ID,
        "authority": canvas_authority_payload(),
        "canonical_mutation_allowed": False,
        "graph_mutation_allowed": False,
        "promotion_requires_gate": True,
        "browser_control_allowed": False,
        "blocked_authority": list(CANVAS_SAVE_BLOCKED_AUTHORITY),
        "blocked_authority_reasons": dict(CANVAS_SAVE_BLOCKED_AUTHORITY_REASONS),
        "target_block_reason": target_block_reason,
        "write_contract": dict(CANVAS_SAVE_WRITE_CONTRACT),
        "write_policy": dict(CANVAS_SAVE_WRITE_POLICY),
        "warnings": [],
    }


def _resolve_canvas_draft_path(vault_root: str | Path, draft_name: str) -> Path:
    vault = Path(vault_root).resolve()
    drafts_root = (vault / CANVAS_DRAFT_DIR).resolve()
    name = str(draft_name or "").strip().replace("\\", "/")
    if not name:
        raise CanvasDraftError("missing_canvas_draft_name", "Canvas draft name is required")
    candidate = (drafts_root / name).resolve()
    try:
        candidate.relative_to(drafts_root)
    except ValueError as exc:
        raise CanvasDraftError("path_traversal", "Canvas drafts must stay under runtime/studio/canvas_drafts") from exc
    if candidate.suffix.lower() != ".json":
        raise CanvasDraftError("json_only", "Canvas drafts must be .json files")
    return candidate


def _authority(value: Any) -> dict[str, bool]:
    if not isinstance(value, dict):
        raise CanvasDraftError("invalid_canvas_document", "authority must be an object")
    authority = {key: value.get(key) for key in CANVAS_AUTHORITY_FLAGS}
    if authority != CANVAS_AUTHORITY_FLAGS:
        raise CanvasDraftError(
            "authority_boundary_violation",
            "Canvas authority flags must exactly match the Phase 10E no-mutation boundary",
        )
    return dict(CANVAS_AUTHORITY_FLAGS)


def _require_keys(value: dict[str, Any], keys: tuple[str, ...], *, code: str) -> None:
    missing = [key for key in keys if key not in value]
    if missing:
        raise CanvasDraftError(code, f"Missing required keys: {', '.join(missing)}")


def _required_string(value: dict[str, Any], key: str, *, code: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise CanvasDraftError(code, f"{key} must be a non-empty string")
    return item


def _optional_string_or_none(value: dict[str, Any], key: str) -> str | None:
    item = value.get(key)
    if item is None:
        return None
    if not isinstance(item, str):
        raise CanvasDraftError("invalid_canvas_document", f"{key} must be a string or null")
    return item


def _required_mapping(value: dict[str, Any], key: str, *, code: str) -> dict[str, Any]:
    item = value.get(key)
    if not isinstance(item, dict):
        raise CanvasDraftError(code, f"{key} must be an object")
    return dict(item)


def _optional_mapping(value: dict[str, Any], key: str) -> dict[str, Any]:
    item = value.get(key, {})
    if item is None:
        return {}
    if not isinstance(item, dict):
        raise CanvasDraftError("invalid_canvas_document", f"{key} must be an object")
    return dict(item)


def _optional_mapping_or_none(value: dict[str, Any], key: str) -> dict[str, Any] | None:
    item = value.get(key)
    if item is None:
        return None
    if not isinstance(item, dict):
        raise CanvasDraftError("invalid_canvas_document", f"{key} must be an object or null")
    return dict(item)


def _validate_xy(value: dict[str, Any], key: str, *, code: str) -> None:
    for coordinate in ("x", "y"):
        if not isinstance(value.get(coordinate), (int, float)):
            raise CanvasDraftError(code, f"{key}.{coordinate} must be numeric")


def _validate_size(value: dict[str, Any], *, code: str) -> None:
    for coordinate in ("width", "height"):
        item = value.get(coordinate)
        if not isinstance(item, (int, float)) or item <= 0:
            raise CanvasDraftError(code, f"size.{coordinate} must be a positive number")
