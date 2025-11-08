"""Stub tiktoken module for testing."""

from __future__ import annotations

from typing import List


def get_encoding(_: str) -> "Encoding":  # pragma: no cover - stub helper
    return Encoding()


class Encoding:  # pragma: no cover - stub container
    def encode(self, text: str, *_, **__) -> List[int]:
        return [len(text)]

    def decode(self, tokens: List[int]) -> str:
        return "".join(chr(token) for token in tokens)
