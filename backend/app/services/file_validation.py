"""Validate uploads for CSV, XLSX, Parquet, JSON."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import chardet

SUPPORTED_EXTENSIONS = {".csv", ".txt", ".tsv", ".xlsx", ".xls", ".parquet", ".json", ".jsonl"}
MAX_BYTES = 512 * 1024 * 1024


@dataclass
class FileValidationResult:
    ok: bool
    format: str
    encoding: str | None = None
    separator: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def detect_format(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in (".csv", ".txt", ".tsv"):
        return "csv"
    if ext in (".xlsx", ".xls"):
        return "xlsx"
    if ext == ".parquet":
        return "parquet"
    if ext in (".json", ".jsonl"):
        return "json"
    return "unknown"


def validate_upload(
    content: bytes,
    filename: str,
    separator_override: str | None = None,
) -> FileValidationResult:
    result = FileValidationResult(ok=True, format=detect_format(filename))

    if len(content) == 0:
        result.ok = False
        result.errors.append("File is empty")
        return result

    if len(content) > MAX_BYTES:
        result.ok = False
        result.errors.append(f"File exceeds {MAX_BYTES // (1024 * 1024)} MB limit")
        return result

    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        result.ok = False
        result.errors.append(
            f"Unsupported file type '{ext}'. Supported: CSV, XLSX, Parquet, JSON"
        )
        return result

    if result.format == "csv":
        from app.services.csv_validation import validate_csv_upload

        csv_result = validate_csv_upload(content, filename, separator_override)
        result.ok = csv_result.ok
        result.errors = csv_result.errors
        result.warnings = csv_result.warnings
        result.encoding = csv_result.encoding
        result.separator = csv_result.separator
        return result

    if result.format == "json":
        try:
            text = content[:4096].decode("utf-8")
        except UnicodeDecodeError:
            detected = chardet.detect(content[:65536])
            result.encoding = detected.get("encoding") or "utf-8"
            result.warnings.append(f"Encoding detected as {result.encoding}")
        else:
            result.encoding = "utf-8"
        if not (text.strip().startswith("[") or text.strip().startswith("{")):
            result.warnings.append("JSON should be an array of objects or a single object")

    if result.format == "parquet" and not content[:4] == b"PAR1":
        result.warnings.append("Parquet magic bytes not found; import may still succeed")

    return result
