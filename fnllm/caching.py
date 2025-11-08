"""Stub cache provider for testing without the fnllm dependency."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Cache:
    name: str | None = None

    def child(self, name: str) -> "Cache":  # pragma: no cover - trivial stub
        return Cache(name=name)

    def get(self, *_: Any, **__: Any) -> None:  # pragma: no cover - trivial stub
        return None

    def set(self, *_: Any, **__: Any) -> None:  # pragma: no cover - trivial stub
        return None
