"""
A fake LLMProvider for tests: returns pre-programmed responses instead of
calling a real API. This is what lets the whole harness be tested without
network access, API keys, or the openai/anthropic packages installed.
"""
from __future__ import annotations

from src.providers.base import LLMProvider


class FakeProvider(LLMProvider):
    """Returns queued responses in order, or a single fixed response for every call."""

    def __init__(self, model_name: str = "fake-model", responses: list[str] | None = None,
                 fixed_response: str | None = None):
        self.model_name = model_name
        self._responses = list(responses) if responses else None
        self._fixed_response = fixed_response
        self.calls: list[tuple[str, str | None]] = []  # records (prompt, system_prompt) for assertions

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        self.calls.append((prompt, system_prompt))
        if self._responses is not None:
            if not self._responses:
                raise AssertionError("FakeProvider ran out of queued responses")
            return self._responses.pop(0)
        if self._fixed_response is not None:
            return self._fixed_response
        raise AssertionError("FakeProvider has no responses configured")
