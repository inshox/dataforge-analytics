"""CSV upload validation before import."""

from dataclasses import dataclass, field
from pathlib import Path

import chardet

ALLOWED_EXTENSIONS = {".csv", ".txt"}
MAX_FILE_BYTES = 512 * 1024 * 1024  # 512 MB


@dataclass
class CsvValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    encoding: str = "utf-8"
    separator: str = ","
    duplicate_columns: list[str] = field(default_factory=list)


def validate_csv_upload(
    content: bytes,
    filename: str,
    separator_override: str | None = None,
) -> CsvValidationResult:
    from app.services.polars_utils import detect_csv_separator

    result = CsvValidationResult(ok=True, separator=separator_override or ",")

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        result.errors.append(f"Unsupported file type '{ext}'. Use .csv")
        result.ok = False

    if len(content) == 0:
        result.errors.append("File is empty")
        result.ok = False
        return result

    if len(content) > MAX_FILE_BYTES:
        result.errors.append(f"File exceeds maximum size ({MAX_FILE_BYTES // (1024 * 1024)} MB)")
        result.ok = False

    detected = chardet.detect(content[:65536])
    enc = (detected.get("encoding") or "utf-8").lower()
    if enc in ("ascii", "utf-8", "utf-8-sig"):
        result.encoding = "utf-8"
    elif enc in ("iso-8859-1", "windows-1252", "latin-1"):
        result.encoding = "latin-1"
        result.warnings.append(f"Detected encoding {enc}; will try latin-1 fallback if needed")
    else:
        result.encoding = enc
        result.warnings.append(f"Detected encoding: {enc}")

    sample = content[:8192]
    result.separator = separator_override or detect_csv_separator(sample)

    try:
        header_line = sample.splitlines()[0].decode(result.encoding, errors="replace")
    except Exception:
        header_line = sample.splitlines()[0].decode("utf-8", errors="replace")
        result.encoding = "utf-8"

    headers = [h.strip().strip('"') for h in header_line.split(result.separator)]
    if not headers or all(h == "" for h in headers):
        result.errors.append("Could not parse header row — check delimiter")
        result.ok = False
    else:
        seen: dict[str, int] = {}
        for h in headers:
            if not h:
                result.warnings.append("Empty column name in header")
                continue
            seen[h] = seen.get(h, 0) + 1
        dups = [k for k, v in seen.items() if v > 1]
        if dups:
            result.duplicate_columns = dups
            result.errors.append(f"Duplicate column names: {', '.join(dups)}")
            result.ok = False

    return result
