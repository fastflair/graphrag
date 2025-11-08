"""Stub structures for chat completion responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class ChatCompletionMessage:
    role: str = "assistant"
    content: str | List[Any] | None = None


@dataclass
class Choice:
    index: int = 0
    message: ChatCompletionMessage = field(default_factory=ChatCompletionMessage)
    finish_reason: str | None = None


@dataclass
class ChatCompletion:
    id: str = "stub"
    choices: list[Choice] = field(default_factory=list)
    usage: Any | None = None
