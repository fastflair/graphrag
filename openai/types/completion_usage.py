"""Stub completion usage structures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PromptTokensDetails:
    cached_tokens: int | None = None


@dataclass
class CompletionTokensDetails:
    reasoning_tokens: int | None = None


@dataclass
class CompletionUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    prompt_tokens_details: PromptTokensDetails | None = None
    completion_tokens_details: CompletionTokensDetails | None = None
