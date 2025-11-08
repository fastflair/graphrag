"""Stub chat completion message."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChatCompletionMessage:
    role: str = "assistant"
    content: str | None = None
