"""Stub implementations of the fnllm OpenAI helper factories."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class _Config:
    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


class OpenAIConfig(_Config):
    pass


class PublicOpenAIConfig(_Config):
    pass


class AzureOpenAIConfig(_Config):
    pass


def _not_available(*_: Any, **__: Any) -> None:
    raise RuntimeError(
        "The lightweight fnllm test stub was invoked. Install the optional "
        "'fnllm' dependency for full functionality."
    )


create_openai_chat_llm = _not_available
create_openai_embedding_llm = _not_available
create_openai_embeddings_llm = _not_available
create_openai_moderation_llm = _not_available
create_openai_client = _not_available
