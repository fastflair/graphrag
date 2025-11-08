"""Stub definitions for fnllm events used during testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LLMEvents:
    """Minimal stand-in for the real fnllm events class."""

    def emit(self, *_: Any, **__: Any) -> None:  # pragma: no cover - trivial stub
        return
