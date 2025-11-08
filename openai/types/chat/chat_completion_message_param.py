"""Stub chat completion message parameter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChatCompletionMessageParam:
    role: str = "user"
    content: str | None = None
