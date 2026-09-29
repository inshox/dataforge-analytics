"""In-memory import cancellation flags."""

from __future__ import annotations

_cancelled: set[str] = set()


def mark_cancelled(dataset_id: str) -> None:
    _cancelled.add(dataset_id)


def is_cancelled(dataset_id: str) -> bool:
    return dataset_id in _cancelled


def clear_cancelled(dataset_id: str) -> None:
    _cancelled.discard(dataset_id)
