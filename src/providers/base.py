"""
Abstract interface every LLM provider must implement.

Keeping this as a small, explicit contract (rather than passing raw SDK
clients around) is what lets the harness, the judge, and the test suite
all work against ANY provider — including a fake one in tests — without
caring which vendor is behind it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Minimal contract: given a prompt (and optional system prompt), return text."""

    #: Human-readable model identifier, used in reports (e.g. "gpt-4o", "claude-opus-4-6")
    model_name: str

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Return the model's text response. Must raise on API failure, not swallow it."""
        raise NotImplementedError
