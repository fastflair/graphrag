"""Minimal LiteLLM stub to satisfy imports during testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class CustomStreamWrapper:  # pragma: no cover - stub container
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


@dataclass
class ModelResponse:
    output: Any | None = None
    choices: list[Any] | None = None


@dataclass
class EmbeddingResponse:
    data: list[Any] | None = None


class AnthropicThinkingParam:  # pragma: no cover - stub container
    pass


class BaseModel:  # pragma: no cover - stub container
    pass


class ChatCompletionAudioParam:  # pragma: no cover - stub container
    pass


class ChatCompletionModality:  # pragma: no cover - stub container
    pass


class ChatCompletionPredictionContentParam:  # pragma: no cover - stub container
    pass


class OpenAIWebSearchOptions:  # pragma: no cover - stub container
    pass


async def acompletion(**_: Any) -> ModelResponse:  # pragma: no cover - stub helper
    return ModelResponse()


def completion(**_: Any) -> ModelResponse:  # pragma: no cover - stub helper
    return ModelResponse()


async def aembedding(**_: Any) -> EmbeddingResponse:  # pragma: no cover - stub helper
    return EmbeddingResponse()


def embedding(**_: Any) -> EmbeddingResponse:  # pragma: no cover - stub helper
    return EmbeddingResponse()


def token_counter(*_: Any, **__: Any) -> int:  # pragma: no cover - stub helper
    return 0


suppress_debug_info = True
