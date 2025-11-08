"""Stub module providing minimal fnllm.base interfaces for testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class JsonStrategy:
    """Enum-like container for json strategies."""

    VALID = "valid"
    LOOSE = "loose"


@dataclass
class RetryStrategy:
    retries: int | None = None


def build_retry_strategy(*_: Any, **__: Any) -> RetryStrategy:  # pragma: no cover - stub helper
    return RetryStrategy()
