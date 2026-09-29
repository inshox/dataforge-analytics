"""Filesystem paths for datasets."""

from pathlib import Path
from uuid import UUID

from app.core.config import get_settings, ensure_data_dirs


def dataset_dir(dataset_id: UUID | str) -> Path:
    base = ensure_data_dirs()
    path = base / "datasets" / str(dataset_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def parquet_path(dataset_id: UUID | str) -> Path:
    return dataset_dir(dataset_id) / "data.parquet"


def upload_path(filename: str) -> Path:
    s = get_settings()
    ensure_data_dirs(s)
    return s.data_dir.resolve() / "uploads" / filename
