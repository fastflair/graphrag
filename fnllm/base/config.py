"""Compatibility shim that mirrors fnllm.base.config symbols."""

from __future__ import annotations

from . import JsonStrategy, RetryStrategy, build_retry_strategy

__all__ = ["JsonStrategy", "RetryStrategy", "build_retry_strategy"]
