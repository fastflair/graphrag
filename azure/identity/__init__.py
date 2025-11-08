"""Stub implementations of azure.identity helpers."""

from __future__ import annotations

from typing import Any, Callable


class DefaultAzureCredential:  # pragma: no cover - trivial stub
    def get_token(self, *_: Any, **__: Any) -> str:
        return "stub-token"


def get_bearer_token_provider(*_: Any, **__: Any) -> Callable[[], str]:  # pragma: no cover - stub
    def _provider() -> str:
        return "stub-token"

    return _provider
