"""Stub chunked chat completion responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChoiceDelta:
    content: str | None = None


@dataclass
class Choice:
    index: int = 0
    delta: ChoiceDelta = field(default_factory=ChoiceDelta)
    finish_reason: str | None = None


@dataclass
class ChatCompletionChunk:
    id: str = "stub-chunk"
    choices: list[Choice] = field(default_factory=list)
