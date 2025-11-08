"""Stub OpenAI chat parameter object used for testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class OpenAIChatParameters:
    """Minimal parameter container matching the interface used in production."""

    def __init__(self, **kwargs: Any) -> None:  # pragma: no cover - trivial container
        for key, value in kwargs.items():
            setattr(self, key, value)
