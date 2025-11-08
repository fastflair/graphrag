"""Stub embedding response structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Usage:
    prompt_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class CreateEmbeddingResponse:
    data: list[Any] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
