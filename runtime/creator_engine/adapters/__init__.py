"""Creator Engine intake adapter contracts."""

from .base import AdapterValidationResult, RecordingCandidate, RecordingIntakeAdapter
from .manual import ManualFileRecordingAdapter

__all__ = [
    "AdapterValidationResult",
    "ManualFileRecordingAdapter",
    "RecordingCandidate",
    "RecordingIntakeAdapter",
]
