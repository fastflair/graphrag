"""File-system helpers for persisting project chat artefacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def ensure_directory(path: Path) -> Path:
    """Create a directory and return it."""

    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Persist a JSON mapping using UTF-8 encoding."""

    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Persist plain text content using UTF-8 encoding."""

    path.write_text(content, encoding="utf-8")
