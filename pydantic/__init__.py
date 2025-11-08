"""Lightweight stub of the pydantic API used in tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


def Field(default: Any = None, *_, default_factory: Callable[[], Any] | None = None, **__) -> Any:
    """Return default values while ignoring validation metadata."""

    if default_factory is not None:
        return default_factory()
    return default


@dataclass
class BaseModel:
    """Minimal drop-in replacement implementing model_dump."""

    def __init__(self, **data: Any) -> None:
        for key, value in data.items():
            setattr(self, key, value)

    def model_dump(self) -> dict[str, Any]:  # pragma: no cover - simple helper
        return self.__dict__.copy()


def model_validator(*_args: Any, **_kwargs: Any):  # pragma: no cover - stub decorator
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        return fn

    return decorator
