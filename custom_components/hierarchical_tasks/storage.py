"""Versioned private JSON file with atomic replacement and surfaced I/O errors.

Disk functions must run in Home Assistant's executor, never its event loop.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .model import TaskError, validate_document

MAX_FILE_BYTES = 2_000_000


def read_document(path: Path) -> dict[str, Any] | None:
    """A malformed file is left intact; it is NEVER replaced with sample data."""
    try:
        with path.open("rb") as handle:
            contents = handle.read(MAX_FILE_BYTES + 1)
    except FileNotFoundError:
        return None
    if len(contents) > MAX_FILE_BYTES:
        raise TaskError("invalid_storage", "Data file exceeds the size limit.")
    try:
        data = json.loads(contents)
    except (ValueError, UnicodeError) as err:
        raise TaskError("invalid_storage", "Invalid JSON. Restore the file from a backup.") from err
    return validate_document(data)


def write_document(path: Path, data: dict[str, Any]) -> None:
    """Write + fsync a temporary file on the same filesystem, then os.replace.

A sudden power loss still depends on the filesystem/hardware. This is not a
substitute for backups. No deferred/batched success acknowledgements are used.
"""
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(encoded) > MAX_FILE_BYTES:
        raise TaskError("invalid_storage", "Data file exceeds the size limit.")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        # mkstemp creates the file with mode 0600 on Unix.
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
