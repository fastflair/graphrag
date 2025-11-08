"""Stub embedding type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Embedding:
    embedding: List[float] | None = None
